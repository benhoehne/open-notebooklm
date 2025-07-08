"""
Podcast generation module containing the core logic for generating podcasts from content.
"""

# Standard library imports
import glob
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Tuple, Optional
import random
import uuid

# Third-party imports
from loguru import logger
from pypdf import PdfReader

# Local imports
from constants import (
    CHARACTER_LIMIT,
    ERROR_MESSAGE_NOT_PDF,
    ERROR_MESSAGE_NO_INPUT,
    ERROR_MESSAGE_READING_PDF,
    ERROR_MESSAGE_TOO_LONG,
    GRADIO_CACHE_DIR,
    GRADIO_CLEAR_CACHE_OLDER_THAN,
    get_voice_assignments,
    get_custom_voice_assignments,
    GOOGLE_CLOUD_API_KEY,
    TEMP_AUDIO_DIR,
)
from prompts import (
    LANGUAGE_MODIFIER,
    LENGTH_MODIFIERS,
    QUESTION_MODIFIER,
    SYSTEM_PROMPT,
    TONE_MODIFIER,
)
from schema import (
    ShortDialogue, MediumDialogue, LongDialogue,
    get_dialogue_schema
)
from utils import generate_podcast_audio, generate_script, parse_url, generate_vtt_content, clear_voice_cache
from h5p_generator import generate_h5p_package

from pydub import AudioSegment


def generate_podcast(
    files: List[str],
    url: Optional[str],
    question: Optional[str],
    tone: Optional[str],
    length: Optional[str],
    language: str,
    host_name: Optional[str] = "Sam",
    guest_name: Optional[str] = None,
    host_gender: str = "random",
    guest_gender: str = "random"
) -> Tuple[str, str, str, str]:
    """Generate the audio and transcript from the PDFs and/or URL."""

    text = ""
    
    # Clear voice cache to ensure fresh voice assignments for this podcast
    clear_voice_cache()
    
    # Get voice assignments based on user preferences
    voice_assignments = get_custom_voice_assignments(host_gender, guest_gender)
    
    # Log voice assignments (now using list-based structure)
    host_voice_sample = list(voice_assignments['Host (Sam)'].values())[0][0] if voice_assignments['Host (Sam)'] else "Unknown"
    guest_voice_sample = list(voice_assignments['Guest'].values())[0][0] if voice_assignments['Guest'] else "Unknown"
    logger.info(f"Voice assignments for this podcast: Host={'Female' if 'HD-F' in host_voice_sample or 'Achernar' in host_voice_sample or 'Aoede' in host_voice_sample else 'Male'}, Guest={'Female' if 'HD-F' in guest_voice_sample or 'Achernar' in guest_voice_sample or 'Aoede' in guest_voice_sample else 'Male'}")

    # Require Google Cloud TTS API key
    if not GOOGLE_CLOUD_API_KEY:
        raise ValueError("Google Cloud TTS API key is required. Please set GOOGLE_CLOUD_API_KEY environment variable.")

    # Check if at least one input is provided
    if not files and not url:
        raise ValueError(ERROR_MESSAGE_NO_INPUT)

    # Process PDFs if any
    if files:
        for file in files:
            if not file.lower().endswith(".pdf"):
                raise ValueError(ERROR_MESSAGE_NOT_PDF)

            try:
                with Path(file).open("rb") as f:
                    reader = PdfReader(f)
                    text += "\n\n".join([page.extract_text() for page in reader.pages])
            except Exception as e:
                raise ValueError(f"{ERROR_MESSAGE_READING_PDF}: {str(e)}")

    # Process URL if provided
    if url:
        try:
            url_text = parse_url(url)
            text += "\n\n" + url_text
        except ValueError as e:
            raise ValueError(str(e))

    # Check total character count
    if len(text) > CHARACTER_LIMIT:
        raise ValueError(ERROR_MESSAGE_TOO_LONG)

    # Modify the system prompt based on the user input
    modified_system_prompt = SYSTEM_PROMPT

    # Update system prompt with custom names
    if host_name and host_name != "Sam":
        modified_system_prompt = modified_system_prompt.replace("Host (Sam)", f"Host ({host_name})")
    
    if question:
        modified_system_prompt += f"\n\n{QUESTION_MODIFIER} {question}"
    if tone:
        modified_system_prompt += f"\n\n{TONE_MODIFIER} {tone}."
    if length:
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS[length]}"
    if language:
        modified_system_prompt += f"\n\n{LANGUAGE_MODIFIER} {language}."

    # Get the appropriate schema and generate the script
    final_guest_name = guest_name if guest_name else "Alex"
    
    # Map length to schema type
    if length == "Short (1-2 min)":
        schema_type = "short"
    elif length == "Medium (3-5 min)":
        schema_type = "medium"
    else:  # Long (10-12 min)
        schema_type = "long"
    
    DialogueSchema = get_dialogue_schema(schema_type)
    llm_output = generate_script(
        modified_system_prompt, 
        text, 
        DialogueSchema,
        host_name=host_name,
        guest_name=final_guest_name
    )

    # Set guest name in output
    if guest_name:
        llm_output.name_of_guest = guest_name
    elif not hasattr(llm_output, 'name_of_guest') or not llm_output.name_of_guest:
        llm_output.name_of_guest = final_guest_name

    logger.info(f"Generated dialogue: {llm_output}")

    # Process the dialogue
    audio_segments = []
    dialogue_items = []
    transcript = ""
    total_characters = 0

    for line in llm_output.dialogue:
        # With proper Pydantic models, we should have objects directly
        line_speaker = line.speaker
        line_text = line.text
            
        # Debug logging to see what we're getting
        logger.info(f"Processing dialogue line - Speaker: '{line_speaker}', Text: '{line_text[:50]}...' (length: {len(line_text)})")
        
        # Skip empty dialogue items
        if not line_speaker or not line_text:
            logger.warning(f"Skipping empty dialogue line - Speaker: '{line_speaker}', Text length: {len(line_text)}")
            continue
            
        logger.info(f"Generating audio for {line_speaker}: {line_text}")
        
        # More flexible speaker matching for transcript
        if 'host' in line_speaker.lower() or line_speaker.lower() == host_name.lower():
            speaker_name = host_name
        else:
            speaker_name = llm_output.name_of_guest
            
        speaker = f"**{speaker_name}**: {line_text}"
        transcript += speaker + "\n\n"
        total_characters += len(line_text)

        # Google TTS expects full language names (e.g., "German")
        language_for_tts = language

        # Get audio file path
        audio_file_path = generate_podcast_audio(
            line_text, line_speaker, language_for_tts, voice_assignments
        )
        # Read the audio file into an AudioSegment
        audio_segment = AudioSegment.from_file(audio_file_path)
        audio_segments.append(audio_segment)
        
        # Store dialogue item for VTT generation
        dialogue_items.append({
            'speaker': speaker_name,
            'text': line_text
        })

    # Concatenate all audio segments
    combined_audio = sum(audio_segments)

    # Export the combined audio to a temporary file
    temporary_directory = GRADIO_CACHE_DIR
    try:
        os.makedirs(temporary_directory, exist_ok=True)
    except (PermissionError, OSError) as e:
        raise ValueError(f"Permission denied: Unable to create temporary directory '{temporary_directory}'. Please ensure the application has write permissions: {e}")

    # Use a more robust approach for creating temporary files on Synology
    unique_filename = f"podcast_{uuid.uuid4().hex}.mp3"
    temp_file_path = os.path.join(temporary_directory, unique_filename)
    
    # Export directly to the specified path
    try:
        combined_audio.export(temp_file_path, format="mp3")
    except (PermissionError, OSError) as e:
        raise ValueError(f"Permission denied: Unable to create audio file '{temp_file_path}'. Please ensure the application has write permissions: {e}")

    # Generate VTT file
    vtt_content = generate_vtt_content(dialogue_items, audio_segments)
    vtt_file_path = temp_file_path.replace('.mp3', '.vtt')
    
    try:
        with open(vtt_file_path, 'w', encoding='utf-8') as vtt_file:
            vtt_file.write(vtt_content)
        logger.info(f"Generated VTT file: {vtt_file_path}")
    except (PermissionError, OSError) as e:
        logger.warning(f"Failed to create VTT file: {e}")
        vtt_file_path = None

    # Delete any files in the temp directory that end with .mp3 and are over a day old
    for file in glob.glob(f"{temporary_directory}*.mp3"):
        if (
            os.path.isfile(file)
            and time.time() - os.path.getmtime(file) > GRADIO_CLEAR_CACHE_OLDER_THAN
        ):
            os.remove(file)

    # Generate H5P package if VTT file was created successfully
    h5p_file_path = None
    if vtt_file_path:
        try:
            # Create a title for the H5P package
            h5p_title = f"Podcast - {host_name} & {llm_output.name_of_guest}"
            
            # Map language code for H5P (use first 2 characters for language code)
            language_code = language.lower()[:2] if language else "en"
            
            h5p_file_path = generate_h5p_package(
                audio_file_path=temp_file_path,
                vtt_file_path=vtt_file_path,
                language=language_code,
                title=h5p_title
            )
            logger.info(f"Generated H5P package: {h5p_file_path}")
        except Exception as e:
            logger.warning(f"Failed to create H5P package: {e}")
            h5p_file_path = None

    logger.info(f"Generated {total_characters} characters of audio")

    return temp_file_path, transcript, vtt_file_path, h5p_file_path


def generate_script_only(
    files: List[str],
    url: Optional[str],
    question: Optional[str],
    tone: Optional[str],
    length: Optional[str],
    language: str,
    host_name: Optional[str] = "Sam",
    guest_name: Optional[str] = None,
) -> Tuple[str, dict]:
    """Generate only the script without audio synthesis."""
    
    text = ""

    # Check if at least one input is provided
    if not files and not url:
        raise ValueError(ERROR_MESSAGE_NO_INPUT)

    # Process PDFs if any
    if files:
        for file in files:
            if not file.lower().endswith(".pdf"):
                raise ValueError(ERROR_MESSAGE_NOT_PDF)

            try:
                with Path(file).open("rb") as f:
                    reader = PdfReader(f)
                    text += "\n\n".join([page.extract_text() for page in reader.pages])
            except Exception as e:
                raise ValueError(f"{ERROR_MESSAGE_READING_PDF}: {str(e)}")

    # Process URL if provided
    if url:
        try:
            url_text = parse_url(url)
            text += "\n\n" + url_text
        except ValueError as e:
            raise ValueError(str(e))

    # Check total character count
    if len(text) > CHARACTER_LIMIT:
        raise ValueError(ERROR_MESSAGE_TOO_LONG)

    # Modify the system prompt based on the user input
    modified_system_prompt = SYSTEM_PROMPT

    # Update system prompt with custom names
    if host_name and host_name != "Sam":
        modified_system_prompt = modified_system_prompt.replace("Host (Sam)", f"Host ({host_name})")
    
    if question:
        modified_system_prompt += f"\n\n{QUESTION_MODIFIER} {question}"
    if tone:
        modified_system_prompt += f"\n\n{TONE_MODIFIER} {tone}."
    if length:
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS[length]}"
    if language:
        modified_system_prompt += f"\n\n{LANGUAGE_MODIFIER} {language}."

    # Get the appropriate schema and generate the script
    final_guest_name = guest_name if guest_name else "Alex"
    
    # Map length to schema type
    if length == "Short (1-2 min)":
        schema_type = "short"
    elif length == "Medium (3-5 min)":
        schema_type = "medium"
    else:  # Long (10-12 min)
        schema_type = "long"
    
    DialogueSchema = get_dialogue_schema(schema_type)
    llm_output = generate_script(
        modified_system_prompt, 
        text, 
        DialogueSchema,
        host_name=host_name,
        guest_name=final_guest_name
    )

    # Set guest name in output
    if guest_name:
        llm_output.name_of_guest = guest_name
    elif not hasattr(llm_output, 'name_of_guest') or not llm_output.name_of_guest:
        llm_output.name_of_guest = final_guest_name

    # Convert dialogue to markdown format for editing
    script_content = f"# Podcast Script\n\n"
    script_content += f"**Host:** {host_name}\n"
    script_content += f"**Guest:** {llm_output.name_of_guest}\n\n"
    script_content += "---\n\n"
    
    for line in llm_output.dialogue:
        # With proper Pydantic models, we should have objects directly
        speaker = line.speaker
        text = line.text
        
        # Debug logging to see what we're getting
        logger.info(f"Processing dialogue line - Speaker: '{speaker}', Text: '{text[:50]}...' (length: {len(text)})")
        
        # More flexible speaker matching
        if speaker and text:  # Only process if both speaker and text exist
            # Check if this is the host
            if 'host' in speaker.lower() or speaker.lower() == host_name.lower():
                speaker_name = host_name
            else:
                speaker_name = llm_output.name_of_guest
            
            script_content += f"**{speaker_name}:** {text}\n\n"
        else:
            logger.warning(f"Skipping empty dialogue line - Speaker: '{speaker}', Text length: {len(text)}")

    # Store generation parameters for later use
    generation_params = {
        'language': language,
        'host_name': host_name,
        'guest_name': llm_output.name_of_guest,
        'length': length
    }

    return script_content, generation_params


def synthesize_audio_from_script(
    script_content: str,
    language: str,
    host_name: str,
    guest_name: str,
    host_gender: str,
    guest_gender: str
) -> Tuple[str, str, str, str]:
    """Synthesize audio from an edited script."""
    
    # Clear voice cache to ensure fresh voice assignments for this podcast
    clear_voice_cache()
    
    # Get voice assignments based on user preferences
    voice_assignments = get_custom_voice_assignments(host_gender, guest_gender)
    
    # Parse the script content to extract dialogue
    lines = script_content.split('\n')
    dialogue_items = []
    transcript = ""
    
    current_speaker = None
    current_text = ""
    
    # Skip everything before the separator
    separator_found = False
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('#'):
            continue
            
        # Check for separator
        if line == '---':
            separator_found = True
            continue
            
        # Skip metadata section before separator
        if not separator_found:
            continue
            
        # Check if this is a speaker line
        if line.startswith('**') and ':**' in line:
            # Save previous dialogue item if exists
            if current_speaker and current_text.strip():
                # Map speaker name back to expected format
                speaker_format = "Host (Sam)" if current_speaker.lower() == host_name.lower() else "Guest"
                dialogue_items.append({
                    'speaker': speaker_format,
                    'text': current_text.strip()
                })
                transcript += f"**{current_speaker}**: {current_text.strip()}\n\n"
            
            # Extract new speaker and start of text
            parts = line.split(':**', 1)
            current_speaker = parts[0].replace('**', '').strip()
            current_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Continue current speaker's text
            if current_text:
                current_text += " " + line
            else:
                current_text = line
    
    # Don't forget the last dialogue item
    if current_speaker and current_text.strip():
        speaker_format = "Host (Sam)" if current_speaker.lower() == host_name.lower() else "Guest"
        dialogue_items.append({
            'speaker': speaker_format,
            'text': current_text.strip()
        })
        transcript += f"**{current_speaker}**: {current_text.strip()}\n\n"

    if not dialogue_items:
        raise ValueError("No dialogue found in the script. Please check the format.")

    # Generate audio for each dialogue item
    audio_segments = []
    total_characters = 0

    for item in dialogue_items:
        logger.info(f"Generating audio for {item['speaker']}: {item['text']}")
        total_characters += len(item['text'])

        # Google TTS expects full language names (e.g., "German")
        language_for_tts = language

        # Get audio file path
        audio_file_path = generate_podcast_audio(
            item['text'], item['speaker'], language_for_tts, voice_assignments
        )
        # Read the audio file into an AudioSegment
        audio_segment = AudioSegment.from_file(audio_file_path)
        audio_segments.append(audio_segment)

    # Concatenate all audio segments
    combined_audio = sum(audio_segments)

    # Export the combined audio to a temporary file
    temporary_directory = GRADIO_CACHE_DIR
    os.makedirs(temporary_directory, exist_ok=True)

    # Use a more robust approach for creating temporary files on Synology
    unique_filename = f"podcast_{uuid.uuid4().hex}.mp3"
    temp_file_path = os.path.join(temporary_directory, unique_filename)
    
    # Export directly to the specified path
    combined_audio.export(temp_file_path, format="mp3")

    # Generate VTT file - create dialogue items with proper speaker names for VTT
    vtt_dialogue_items = []
    for item in dialogue_items:
        # Extract clean speaker name from the speaker format
        if item['speaker'] == "Host (Sam)":
            speaker_name = host_name
        else:
            speaker_name = guest_name
        
        vtt_dialogue_items.append({
            'speaker': speaker_name,
            'text': item['text']
        })
    
    vtt_content = generate_vtt_content(vtt_dialogue_items, audio_segments)
    vtt_file_path = temp_file_path.replace('.mp3', '.vtt')
    
    try:
        with open(vtt_file_path, 'w', encoding='utf-8') as vtt_file:
            vtt_file.write(vtt_content)
        logger.info(f"Generated VTT file: {vtt_file_path}")
    except (PermissionError, OSError) as e:
        logger.warning(f"Failed to create VTT file: {e}")
        vtt_file_path = None

    # Generate H5P package if VTT file was created successfully
    h5p_file_path = None
    if vtt_file_path:
        try:
            # Create a title for the H5P package
            h5p_title = f"Podcast - {host_name} & {guest_name}"
            
            # Map language code for H5P (use first 2 characters for language code)
            language_code = language.lower()[:2] if language else "en"
            
            h5p_file_path = generate_h5p_package(
                audio_file_path=temp_file_path,
                vtt_file_path=vtt_file_path,
                language=language_code,
                title=h5p_title
            )
            logger.info(f"Generated H5P package: {h5p_file_path}")
        except Exception as e:
            logger.warning(f"Failed to create H5P package: {e}")
            h5p_file_path = None

    logger.info(f"Generated {total_characters} characters of audio")

    return temp_file_path, transcript, vtt_file_path, h5p_file_path

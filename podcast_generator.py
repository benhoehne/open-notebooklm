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


def generate_separate_channels(audio_segments, dialogue_items, speaker_names):
    """
    Generate separate audio tracks for each speaker with proper timing/pauses.
    
    Args:
        audio_segments: List of AudioSegment objects for each dialogue line
        dialogue_items: List of dialogue items with speaker and text info
        speaker_names: Dict mapping speaker roles to actual names (e.g., {'host': 'Sam', 'guest': 'Alex'})
    
    Returns:
        tuple: (host_channel, guest_channel) - AudioSegment objects for each speaker
    """
    if len(audio_segments) != len(dialogue_items):
        raise ValueError("Number of audio segments must match number of dialogue items")
    
    host_segments = []
    guest_segments = []
    
    # Get speaker names for comparison
    host_name = speaker_names.get('host', 'Sam')
    guest_name = speaker_names.get('guest', 'Alex')
    
    logger.info(f"Creating separate channels for host: {host_name}, guest: {guest_name}")
    
    for i, (segment, dialogue_item) in enumerate(zip(audio_segments, dialogue_items)):
        speaker = dialogue_item['speaker']
        segment_duration = len(segment)  # Duration in milliseconds
        
        # Create silence segment of the same duration
        silence = AudioSegment.silent(duration=segment_duration)
        
        # Determine which speaker this segment belongs to
        if speaker == host_name:
            # Host is speaking - add audio to host channel, silence to guest channel
            host_segments.append(segment)
            guest_segments.append(silence)
            logger.debug(f"Segment {i+1}: Host speaking ({segment_duration}ms)")
        else:
            # Guest is speaking - add audio to guest channel, silence to host channel
            host_segments.append(silence)
            guest_segments.append(segment)
            logger.debug(f"Segment {i+1}: Guest speaking ({segment_duration}ms)")
    
    # Combine all segments for each speaker
    host_channel = sum(host_segments) if host_segments else AudioSegment.empty()
    guest_channel = sum(guest_segments) if guest_segments else AudioSegment.empty()
    
    logger.info(f"Generated separate channels - Host: {len(host_channel)}ms, Guest: {len(guest_channel)}ms")
    
    return host_channel, guest_channel


def generate_podcast(
    files: List[str],
    url: Optional[str],
    question: Optional[str],
    tone: Optional[str],
    length: Optional[str],
    language: str,
    host_name: Optional[str] = "Sam",
    guest_name: Optional[str] = None,
    voice_provider: str = "google_tts",
    host_voice: str = "random",
    guest_voice: str = "random"
) -> Tuple[str, str, str, str, str, str]:
    """Generate the audio and transcript from the PDFs and/or URL."""

    text = ""
    
    # Clear voice cache to ensure fresh voice assignments for this podcast
    clear_voice_cache()
    
    # Import voice manager for new voice system
    from voice_manager import voice_manager
    
    # Handle voice assignments using new voice system
    if host_voice in ['random', 'male', 'female'] or guest_voice in ['random', 'male', 'female']:
        # Use legacy gender-based assignment for compatibility
        host_gender = 'male' if host_voice == 'male' else 'female' if host_voice == 'female' else 'random'
        guest_gender = 'male' if guest_voice == 'male' else 'female' if guest_voice == 'female' else 'random'
        
        # Get voice assignments based on user preferences and provider
        from constants import get_custom_voice_assignments
        voice_assignments = get_custom_voice_assignments(host_gender, guest_gender, voice_provider)
    else:
        # Use specific voice IDs
        # Get voice data for host
        host_voice_data = voice_manager.get_voice_by_id(voice_provider, language, host_voice)
        guest_voice_data = voice_manager.get_voice_by_id(voice_provider, language, guest_voice)
        
        # Fallback to random if specific voices not found
        if not host_voice_data:
            host_voice_data = voice_manager.get_random_voice(voice_provider, language, 'random')
        if not guest_voice_data:
            guest_voice_data = voice_manager.get_random_voice(voice_provider, language, 'random')
        
        # Create voice assignments in the format expected by the audio generation
        if voice_provider == "elevenlabs":
            voice_assignments = {
                "Host (Sam)": {language: [host_voice_data['id']] if host_voice_data else []},
                "Guest": {language: [guest_voice_data['id']] if guest_voice_data else []}
            }
        else:  # google_tts
            voice_assignments = {
                "Host (Sam)": {language: [host_voice_data['id']] if host_voice_data else []},
                "Guest": {language: [guest_voice_data['id']] if guest_voice_data else []}
            }
    
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

    # Generate separate channels for each speaker
    speaker_names = {'host': host_name, 'guest': llm_output.name_of_guest}
    host_channel, guest_channel = generate_separate_channels(audio_segments, dialogue_items, speaker_names)

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
    
    # Export separate channel files
    host_channel_path = temp_file_path.replace('.mp3', '_host.mp3')
    guest_channel_path = temp_file_path.replace('.mp3', '_guest.mp3')
    
    try:
        host_channel.export(host_channel_path, format="mp3")
        guest_channel.export(guest_channel_path, format="mp3")
        logger.info(f"Generated separate channel files: {host_channel_path}, {guest_channel_path}")
    except (PermissionError, OSError) as e:
        logger.warning(f"Failed to create separate channel files: {e}")
        host_channel_path = None
        guest_channel_path = None

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

    return temp_file_path, transcript, vtt_file_path, h5p_file_path, host_channel_path, guest_channel_path


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
    voice_provider: str = "google_tts",
    host_voice: str = "random",
    guest_voice: str = "random"
) -> Tuple[str, str, str, str, str, str]:
    """Synthesize audio from an edited script."""
    
    # Clear voice cache to ensure fresh voice assignments for this podcast
    clear_voice_cache()
    
    # Import voice manager for new voice system
    from voice_manager import voice_manager
    
    # Handle voice assignments using new voice system
    if host_voice in ['random', 'male', 'female'] or guest_voice in ['random', 'male', 'female']:
        # Use legacy gender-based assignment for compatibility
        host_gender = 'male' if host_voice == 'male' else 'female' if host_voice == 'female' else 'random'
        guest_gender = 'male' if guest_voice == 'male' else 'female' if guest_voice == 'female' else 'random'
        
        # Get voice assignments based on user preferences and provider
        from constants import get_custom_voice_assignments
        voice_assignments = get_custom_voice_assignments(host_gender, guest_gender, voice_provider)
    else:
        # Use specific voice IDs
        # Get voice data for host
        host_voice_data = voice_manager.get_voice_by_id(voice_provider, language, host_voice)
        guest_voice_data = voice_manager.get_voice_by_id(voice_provider, language, guest_voice)
        
        # Fallback to random if specific voices not found
        if not host_voice_data:
            host_voice_data = voice_manager.get_random_voice(voice_provider, language, 'random')
        if not guest_voice_data:
            guest_voice_data = voice_manager.get_random_voice(voice_provider, language, 'random')
        
        # Create voice assignments in the format expected by the audio generation
        if voice_provider == "elevenlabs":
            voice_assignments = {
                "Host (Sam)": {language: [host_voice_data['id']] if host_voice_data else []},
                "Guest": {language: [guest_voice_data['id']] if guest_voice_data else []}
            }
        else:  # google_tts
            voice_assignments = {
                "Host (Sam)": {language: [host_voice_data['id']] if host_voice_data else []},
                "Guest": {language: [guest_voice_data['id']] if guest_voice_data else []}
            }
        
        # Log voice assignments for debugging
        logger.info(f"Voice assignments created: {voice_assignments}")
        logger.info(f"Host voice: {host_voice_data}")
        logger.info(f"Guest voice: {guest_voice_data}")
    
    # Parse the script content to extract dialogue
    lines = script_content.split('\n')
    dialogue_items = []
    transcript = ""
    
    current_speaker = None
    current_text = ""
    
    # Extract actual host and guest names from the script header
    actual_host_name = None
    actual_guest_name = None
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
            
        # Parse metadata section before separator to get actual names
        if not separator_found:
            if line.startswith('**Host:**'):
                actual_host_name = line.replace('**Host:**', '').strip()
                logger.info(f"Extracted host name from script: {actual_host_name}")
            elif line.startswith('**Guest:**'):
                actual_guest_name = line.replace('**Guest:**', '').strip()
                logger.info(f"Extracted guest name from script: {actual_guest_name}")
            continue
            
        # Check if this is a speaker line
        if line.startswith('**') and ':**' in line:
            # Save previous dialogue item if exists
            if current_speaker and current_text.strip():
                # Map speaker name back to expected format using actual names
                speaker_format = "Host (Sam)" if (actual_host_name and current_speaker.lower() == actual_host_name.lower()) else "Guest"
                logger.info(f"Speaker mapping: '{current_speaker}' -> '{speaker_format}' (actual_host_name: {actual_host_name})")
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
        speaker_format = "Host (Sam)" if (actual_host_name and current_speaker.lower() == actual_host_name.lower()) else "Guest"
        logger.info(f"Final speaker mapping: '{current_speaker}' -> '{speaker_format}' (actual_host_name: {actual_host_name})")
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
    
    # Generate separate channels for each speaker
    speaker_names = {'host': host_name, 'guest': guest_name}
    # Use VTT dialogue items with proper speaker names for separate channels
    host_channel, guest_channel = generate_separate_channels(audio_segments, vtt_dialogue_items, speaker_names)

    # Export the combined audio to a temporary file
    temporary_directory = GRADIO_CACHE_DIR
    os.makedirs(temporary_directory, exist_ok=True)

    # Use a more robust approach for creating temporary files on Synology
    unique_filename = f"podcast_{uuid.uuid4().hex}.mp3"
    temp_file_path = os.path.join(temporary_directory, unique_filename)
    
    # Export directly to the specified path
    combined_audio.export(temp_file_path, format="mp3")
    
    # Export separate channel files
    host_channel_path = temp_file_path.replace('.mp3', '_host.mp3')
    guest_channel_path = temp_file_path.replace('.mp3', '_guest.mp3')
    
    try:
        host_channel.export(host_channel_path, format="mp3")
        guest_channel.export(guest_channel_path, format="mp3")
        logger.info(f"Generated separate channel files: {host_channel_path}, {guest_channel_path}")
    except (PermissionError, OSError) as e:
        logger.warning(f"Failed to create separate channel files: {e}")
        host_channel_path = None
        guest_channel_path = None

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

    return temp_file_path, transcript, vtt_file_path, h5p_file_path, host_channel_path, guest_channel_path

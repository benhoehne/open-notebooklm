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
    create_short_dialogue_schema, create_medium_dialogue_schema, create_long_dialogue_schema
)
from utils import generate_podcast_audio, generate_script, parse_url

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
) -> Tuple[str, str]:
    """Generate the audio and transcript from the PDFs and/or URL."""

    text = ""
    
    # Get voice assignments based on user preferences
    voice_assignments = get_custom_voice_assignments(host_gender, guest_gender)
    logger.info(f"Voice assignments for this podcast: Host={'Female' if 'HD-F' in list(voice_assignments['Host (Sam)'].values())[0] else 'Male'}, Guest={'Female' if 'HD-F' in list(voice_assignments['Guest'].values())[0] else 'Male'}")

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

    # Call the LLM with dynamic schema based on host name
    if length == "Short (1-2 min)":
        DialogueSchema = create_short_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)
    elif length == "Medium (3-5 min)":
        DialogueSchema = create_medium_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)
    else:  # Long (10-12 min)
        DialogueSchema = create_long_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)

    # Use custom guest name if provided
    if guest_name:
        llm_output.name_of_guest = guest_name

    logger.info(f"Generated dialogue: {llm_output}")

    # Process the dialogue
    audio_segments = []
    transcript = ""
    total_characters = 0

    for line in llm_output.dialogue:
        logger.info(f"Generating audio for {line.speaker}: {line.text}")
        
        # Update speaker name in transcript
        speaker_name = host_name if line.speaker == f"Host ({host_name})" else llm_output.name_of_guest
        if line.speaker == f"Host ({host_name})":
            speaker = f"**{speaker_name}**: {line.text}"
        else:
            speaker = f"**{speaker_name}**: {line.text}"
        transcript += speaker + "\n\n"
        total_characters += len(line.text)

        # Google TTS expects full language names (e.g., "German")
        language_for_tts = language

        # Get audio file path
        audio_file_path = generate_podcast_audio(
            line.text, line.speaker, language_for_tts, voice_assignments
        )
        # Read the audio file into an AudioSegment
        audio_segment = AudioSegment.from_file(audio_file_path)
        audio_segments.append(audio_segment)

    # Concatenate all audio segments
    combined_audio = sum(audio_segments)

    # Export the combined audio to a temporary file
    temporary_directory = GRADIO_CACHE_DIR
    os.makedirs(temporary_directory, exist_ok=True)

    temporary_file = NamedTemporaryFile(
        dir=temporary_directory,
        delete=False,
        suffix=".mp3",
    )
    combined_audio.export(temporary_file.name, format="mp3")

    # Delete any files in the temp directory that end with .mp3 and are over a day old
    for file in glob.glob(f"{temporary_directory}*.mp3"):
        if (
            os.path.isfile(file)
            and time.time() - os.path.getmtime(file) > GRADIO_CLEAR_CACHE_OLDER_THAN
        ):
            os.remove(file)

    logger.info(f"Generated {total_characters} characters of audio")

    return temporary_file.name, transcript


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

    # Call the LLM with dynamic schema based on host name
    if length == "Short (1-2 min)":
        DialogueSchema = create_short_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)
    elif length == "Medium (3-5 min)":
        DialogueSchema = create_medium_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)
    else:  # Long (10-12 min)
        DialogueSchema = create_long_dialogue_schema(host_name)
        llm_output = generate_script(modified_system_prompt, text, DialogueSchema)

    # Use custom guest name if provided
    if guest_name:
        llm_output.name_of_guest = guest_name

    # Convert dialogue to markdown format for editing
    script_content = f"# Podcast Script\n\n"
    script_content += f"**Host:** {host_name}\n"
    script_content += f"**Guest:** {llm_output.name_of_guest}\n\n"
    script_content += "---\n\n"
    
    for line in llm_output.dialogue:
        speaker_name = host_name if line.speaker == f"Host ({host_name})" else llm_output.name_of_guest
        script_content += f"**{speaker_name}:** {line.text}\n\n"

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
) -> Tuple[str, str]:
    """Synthesize audio from an edited script."""
    
    # Get voice assignments based on user preferences
    voice_assignments = get_custom_voice_assignments(host_gender, guest_gender)
    
    # Parse the script content to extract dialogue
    lines = script_content.split('\n')
    dialogue_items = []
    transcript = ""
    
    current_speaker = None
    current_text = ""
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line == '---':
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

    temporary_file = NamedTemporaryFile(
        dir=temporary_directory,
        delete=False,
        suffix=".mp3",
    )
    combined_audio.export(temporary_file.name, format="mp3")

    logger.info(f"Generated {total_characters} characters of audio")

    return temporary_file.name, transcript 
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
from pydub import AudioSegment

# Local imports
from constants import (
    CHARACTER_LIMIT,
    ERROR_MESSAGE_NOT_PDF,
    ERROR_MESSAGE_NO_INPUT,
    ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS,
    ERROR_MESSAGE_READING_PDF,
    ERROR_MESSAGE_TOO_LONG,
    GRADIO_CACHE_DIR,
    GRADIO_CLEAR_CACHE_OLDER_THAN,
    MELO_TTS_LANGUAGE_MAPPING,
    NOT_SUPPORTED_IN_MELO_TTS,
    SUNO_LANGUAGE_MAPPING,
    get_voice_assignments,
    GOOGLE_CLOUD_API_KEY,
)
from prompts import (
    LANGUAGE_MODIFIER,
    LENGTH_MODIFIERS,
    QUESTION_MODIFIER,
    SYSTEM_PROMPT,
    TONE_MODIFIER,
)
from schema import ShortDialogue, MediumDialogue, LongDialogue
from utils import generate_podcast_audio, generate_script, parse_url


def generate_podcast(
    files: List[str],
    url: Optional[str],
    question: Optional[str],
    tone: Optional[str],
    length: Optional[str],
    language: str,
    use_advanced_audio: bool,
) -> Tuple[str, str]:
    """Generate the audio and transcript from the PDFs and/or URL."""

    text = ""

    # Choose random number from 0 to 8
    random_voice_number = random.randint(0, 8)  # this is for suno model
    
    # Get fresh voice assignments for this podcast (randomizes host/guest genders)
    voice_assignments = get_voice_assignments()
    logger.info(f"Voice assignments for this podcast: Host={'Female' if 'HD-F' in list(voice_assignments['Host (Sam)'].values())[0] else 'Male'}, Guest={'Female' if 'HD-F' in list(voice_assignments['Guest'].values())[0] else 'Male'}")

    # Only check language support if Google Cloud TTS is not available and advanced audio is not enabled
    # Google Cloud TTS supports many more languages than MeloTTS
    if not GOOGLE_CLOUD_API_KEY and not use_advanced_audio and language in NOT_SUPPORTED_IN_MELO_TTS:
        raise ValueError(ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS)

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

    if question:
        modified_system_prompt += f"\n\n{QUESTION_MODIFIER} {question}"
    if tone:
        modified_system_prompt += f"\n\n{TONE_MODIFIER} {tone}."
    if length:
        modified_system_prompt += f"\n\n{LENGTH_MODIFIERS[length]}"
    if language:
        modified_system_prompt += f"\n\n{LANGUAGE_MODIFIER} {language}."

    # Call the LLM
    if length == "Short (1-2 min)":
        llm_output = generate_script(modified_system_prompt, text, ShortDialogue)
    elif length == "Medium (3-5 min)":
        llm_output = generate_script(modified_system_prompt, text, MediumDialogue)
    else:  # Long (10-12 min)
        llm_output = generate_script(modified_system_prompt, text, LongDialogue)

    logger.info(f"Generated dialogue: {llm_output}")

    # Process the dialogue
    audio_segments = []
    transcript = ""
    total_characters = 0

    for line in llm_output.dialogue:
        logger.info(f"Generating audio for {line.speaker}: {line.text}")
        if line.speaker == "Host (Sam)":
            speaker = f"**Host**: {line.text}"
        else:
            speaker = f"**{llm_output.name_of_guest}**: {line.text}"
        transcript += speaker + "\n\n"
        total_characters += len(line.text)

        # Handle language parameter based on TTS engine availability
        if GOOGLE_CLOUD_API_KEY:
            # Google TTS expects full language names (e.g., "German")
            language_for_tts = language
        elif use_advanced_audio:
            # Bark expects language codes (e.g., "de")
            language_for_tts = SUNO_LANGUAGE_MAPPING[language]
        else:
            # MeloTTS expects specific language codes (e.g., "DE")
            language_code = SUNO_LANGUAGE_MAPPING[language]
            language_for_tts = MELO_TTS_LANGUAGE_MAPPING[language_code]

        # Get audio file path
        audio_file_path = generate_podcast_audio(
            line.text, line.speaker, language_for_tts, use_advanced_audio, random_voice_number, voice_assignments
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
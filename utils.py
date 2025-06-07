"""
utils.py

Functions:
- generate_script: Get the dialogue from the LLM.
- call_llm: Call the LLM with the given prompt and dialogue format.
- parse_url: Parse the given URL and return the text content.
- generate_podcast_audio: Generate audio for podcast using Google Cloud Text-to-Speech.
- _use_google_tts: Generate audio using Google Cloud TTS with Chirp HD voices.
"""

# Standard library imports
import time
from typing import Any, Union

# Third-party imports
import requests
import google.genai as genai
from google.cloud import texttospeech

# Local imports
from constants import (
    GEMINI_API_KEY,
    GEMINI_MODEL_ID,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GOOGLE_CLOUD_API_KEY,
    GOOGLE_TTS_VOICES,
    GOOGLE_TTS_RETRY_ATTEMPTS,
    GOOGLE_TTS_RETRY_DELAY,
    JINA_READER_URL,
    JINA_RETRY_ATTEMPTS,
    JINA_RETRY_DELAY,
)
from schema import ShortDialogue, MediumDialogue

# Initialize Google Gemini client with the new Gen AI SDK
# Only initialize if API key is available
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize Google Cloud Text-to-Speech client
# Only initialize if API key is available
google_tts_client = None
if GOOGLE_CLOUD_API_KEY:
    google_tts_client = texttospeech.TextToSpeechClient(
        client_options={"api_key": GOOGLE_CLOUD_API_KEY}
    )


def generate_script(
    system_prompt: str,
    input_text: str,
    output_model: Union[ShortDialogue, MediumDialogue],
) -> Union[ShortDialogue, MediumDialogue]:
    """Get the dialogue from the LLM."""

    # Call the LLM for the first time
    first_draft_dialogue = call_llm(system_prompt, input_text, output_model)

    # Call the LLM a second time to improve the dialogue
    system_prompt_with_dialogue = f"{system_prompt}\n\nHere is the first draft of the dialogue you provided:\n\n{first_draft_dialogue.model_dump_json()}."
    final_dialogue = call_llm(system_prompt_with_dialogue, "Please improve the dialogue. Make it more natural and engaging.", output_model)

    return final_dialogue


def call_llm(system_prompt: str, text: str, dialogue_format: Any) -> Any:
    """Call the LLM with the given prompt and dialogue format."""
    if not gemini_client:
        raise ValueError("Gemini client not initialized. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
    
    # Combine system prompt and user text for Gemini
    combined_prompt = f"{system_prompt}\n\nUser Input:\n{text}"
    
    # Use the new Google Gen AI SDK with structured output (correct format)
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL_ID,
        contents=combined_prompt,
        config={
            "temperature": GEMINI_TEMPERATURE,
            "max_output_tokens": GEMINI_MAX_TOKENS,
            "response_mime_type": "application/json",
            "response_schema": dialogue_format,
        }
    )
    
    # Use the parsed response directly (recommended approach)
    if hasattr(response, 'parsed') and response.parsed is not None:
        return response.parsed
    
    # Fallback: Parse the response text manually if .parsed is not available
    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]  # Remove ```json
    if response_text.endswith('```'):
        response_text = response_text[:-3]  # Remove ```
    response_text = response_text.strip()
    
    return dialogue_format.model_validate_json(response_text)


def parse_url(url: str) -> str:
    """Parse the given URL and return the text content."""
    for attempt in range(JINA_RETRY_ATTEMPTS):
        try:
            full_url = f"{JINA_READER_URL}{url}"
            response = requests.get(full_url, timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes
            break
        except requests.RequestException as e:
            if attempt == JINA_RETRY_ATTEMPTS - 1:  # Last attempt
                raise ValueError(
                    f"Failed to fetch URL after {JINA_RETRY_ATTEMPTS} attempts: {e}"
                ) from e
            time.sleep(JINA_RETRY_DELAY)  # Wait for X second before retrying
    return response.text


def generate_podcast_audio(
    text: str, speaker: str, language: str, voice_assignments: dict = None
) -> str:
    """Generate audio for podcast using Google Cloud Text-to-Speech."""
    if not google_tts_client:
        raise ValueError("Google Cloud TTS client not initialized. Please set GOOGLE_CLOUD_API_KEY environment variable.")
    
    return _use_google_tts(text, speaker, language, voice_assignments)


def _use_google_tts(text: str, speaker: str, language: str, voice_assignments: dict = None) -> str:
    """Generate audio using Google Cloud Text-to-Speech with Chirp HD voices."""
    if not google_tts_client:
        raise ValueError("Google Cloud TTS client not initialized. Please set GOOGLE_CLOUD_API_KEY environment variable.")
    
    # Use provided voice assignments or fallback to the default
    voices_to_use = voice_assignments if voice_assignments else GOOGLE_TTS_VOICES
    
    # Get the appropriate Chirp HD voice for the speaker and language
    voice_name = voices_to_use.get(speaker, {}).get(language)
    if not voice_name:
        # Fallback to English if language not supported
        voice_name = voices_to_use.get(speaker, {}).get("English", "en-US-Chirp-HD-F")
    
    # Extract language code from voice name (e.g., "en-US" from "en-US-Chirp-HD-F")
    language_code = '-'.join(voice_name.split('-')[:2])
    
    for attempt in range(GOOGLE_TTS_RETRY_ATTEMPTS):
        try:
            # Set up the synthesis input (plain text only for Chirp HD voices)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            # Configure the audio output (Chirp HD voices don't support A-Law encoding)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Generate the speech
            response = google_tts_client.synthesize_speech(
                input=synthesis_input, 
                voice=voice, 
                audio_config=audio_config
            )
            
            # Save the audio to a file
            import tempfile
            import os
            
            # Create a temporary file with .mp3 extension
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(response.audio_content)
                temp_file_path = temp_file.name
            
            return temp_file_path
            
        except Exception as e:
            if attempt == GOOGLE_TTS_RETRY_ATTEMPTS - 1:  # Last attempt
                raise Exception(f"Google Cloud TTS failed after {GOOGLE_TTS_RETRY_ATTEMPTS} attempts: {e}")
            time.sleep(GOOGLE_TTS_RETRY_DELAY)




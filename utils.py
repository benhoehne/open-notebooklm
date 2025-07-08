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
import glob

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
    TEMP_AUDIO_DIR,
)
from schema import ShortDialogue, MediumDialogue, LongDialogue

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
    output_model: Union[ShortDialogue, MediumDialogue, LongDialogue],
    host_name: str = "Sam",
    guest_name: str = "Alex"
) -> Union[ShortDialogue, MediumDialogue, LongDialogue]:
    """Get the dialogue from the LLM with structured output."""
    
    # Add speaker name constraints to the system prompt
    enhanced_system_prompt = f"""{system_prompt}

CRITICAL REQUIREMENTS:
- Use EXACTLY these speaker names in the dialogue:
  - Host: "{host_name}"
  - Guest: "{guest_name}"
- The 'name_of_guest' field should be set to: "{guest_name}"
- Every dialogue item must have non-empty text (no empty strings)
- Do not use generic names like "Dr. Anya Sharma" - use the specified names only
- Generate the appropriate number of dialogue items based on the requested length
- Ensure each dialogue item contributes meaningfully to the conversation
"""

    # Call the LLM for the first time with a shorter timeout for faster response
    print("Generating initial script draft...")
    first_draft_dialogue = call_llm(enhanced_system_prompt, input_text, output_model, timeout=45)

    # Try to improve the dialogue with a second call, but make it optional
    # If it fails or times out, we'll use the first draft
    try:
        print("Improving script quality...")
        system_prompt_with_dialogue = f"""{enhanced_system_prompt}

Here is the first draft of the dialogue you provided:
{first_draft_dialogue.model_dump_json()}

MAINTAIN THE SAME SPEAKER NAMES: Host="{host_name}", Guest="{guest_name}"
"""
        final_dialogue = call_llm(
            system_prompt_with_dialogue, 
            "Please improve the dialogue. Make it more natural and engaging. Keep the same speaker names and ensure all text fields are non-empty.", 
            output_model,
            timeout=30  # Shorter timeout for the improvement call
        )
        print("Script improvement completed successfully.")
        return final_dialogue
        
    except Exception as e:
        print(f"Script improvement failed ({str(e)}), using initial draft.")
        # If the second call fails, return the first draft
        return first_draft_dialogue


def call_llm(system_prompt: str, text: str, dialogue_format: Any, timeout: int = 60) -> Any:
    """Call the LLM with the given prompt and dialogue format."""
    if not gemini_client:
        raise ValueError("Gemini client not initialized. Please set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
    
    # Combine system prompt and user text for Gemini
    combined_prompt = f"{system_prompt}\n\nUser Input:\n{text}"
    
    import signal
    import threading
    
    class TimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise TimeoutError("LLM call timed out")
    
    result = None
    exception = None
    
    def make_request():
        nonlocal result, exception
        try:
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
                result = response.parsed
            else:
                # Fallback: Parse the response text manually if .parsed is not available
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove ```
                response_text = response_text.strip()
                
                result = dialogue_format.model_validate_json(response_text)
        except Exception as e:
            exception = e
    
    # Use threading for timeout handling (more reliable than signal on all platforms)
    thread = threading.Thread(target=make_request)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread is still running, which means it timed out
        raise TimeoutError(f"LLM call timed out after {timeout} seconds")
    
    if exception:
        raise exception
    
    if result is None:
        raise Exception("LLM call failed without returning a result")
    
    return result


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


def clear_voice_cache():
    """Clear the voice cache to ensure fresh voice assignments for new podcasts."""
    if hasattr(_use_google_tts, '_voice_cache'):
        _use_google_tts._voice_cache.clear()


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
    
    # Get the appropriate voice for the speaker and language
    # voices_to_use[speaker] now contains a dict with language->list mappings
    speaker_voices = voices_to_use.get(speaker, {})
    
    # Get list of voices for this language
    voice_list = speaker_voices.get(language, [])
    if not voice_list:
        # Fallback to English if language not supported
        voice_list = speaker_voices.get("English", ["en-US-Chirp-HD-F"])
    
    # Check if we have a selected voice for this speaker/language combination stored
    # This ensures consistent voice selection throughout the podcast
    cache_key = f"{speaker}_{language}"
    if not hasattr(_use_google_tts, '_voice_cache'):
        _use_google_tts._voice_cache = {}
    
    if cache_key in _use_google_tts._voice_cache:
        voice_name = _use_google_tts._voice_cache[cache_key]
    else:
        # Select a voice that's not already used by other speakers
        import random
        used_voices = set(_use_google_tts._voice_cache.values())
        available_voices = [v for v in voice_list if v not in used_voices]
        
        # If all voices are used, fall back to any voice (shouldn't happen with 4 voices per gender)
        if not available_voices:
            available_voices = voice_list
            
        voice_name = random.choice(available_voices)
        _use_google_tts._voice_cache[cache_key] = voice_name
    
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
            import uuid
            
            # Ensure our custom temp directory exists and is writable
            os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
            
            # Create a unique filename to avoid conflicts
            unique_filename = f"tts_audio_{uuid.uuid4().hex}.mp3"
            temp_file_path = os.path.join(TEMP_AUDIO_DIR, unique_filename)
            
            # Write the audio content directly to the file
            try:
                with open(temp_file_path, 'wb') as audio_file:
                    audio_file.write(response.audio_content)
            except (PermissionError, OSError) as e:
                raise Exception(f"Permission denied: Unable to create temporary audio file. Please ensure the application has write permissions to the temporary directory: {e}")
            
            return temp_file_path
            
        except Exception as e:
            if attempt == GOOGLE_TTS_RETRY_ATTEMPTS - 1:  # Last attempt
                raise Exception(f"Google Cloud TTS failed after {GOOGLE_TTS_RETRY_ATTEMPTS} attempts: {e}")
            time.sleep(GOOGLE_TTS_RETRY_DELAY)


def generate_vtt_content(dialogue_items, audio_segments):
    """Generate WebVTT content from dialogue items and their corresponding audio segments."""
    vtt_content = "WEBVTT\n\n"
    
    current_time = 0.0  # Start time in seconds
    
    for i, (dialogue_item, audio_segment) in enumerate(zip(dialogue_items, audio_segments)):
        # Calculate start and end times
        start_time = current_time
        duration = len(audio_segment) / 1000.0  # Convert milliseconds to seconds
        end_time = start_time + duration
        
        # Format timestamps as HH:MM:SS.mmm
        start_timestamp = format_vtt_timestamp(start_time)
        end_timestamp = format_vtt_timestamp(end_time)
        
        # Extract speaker name and text
        speaker_name = dialogue_item.get('speaker', 'Unknown')
        text = dialogue_item.get('text', '')
        
        # Add VTT cue
        vtt_content += f"{i + 1}\n"
        vtt_content += f"{start_timestamp} --> {end_timestamp}\n"
        vtt_content += f"<v {speaker_name}>{text}\n\n"
        
        # Update current time for next segment
        current_time = end_time
    
    return vtt_content


def format_vtt_timestamp(seconds):
    """Format seconds as VTT timestamp (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def cleanup_temp_audio_files(max_age_hours=24):
    """Clean up old temporary audio files to prevent disk space issues on Synology."""
    try:
        import os
        import time
        
        if not os.path.exists(TEMP_AUDIO_DIR):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Clean up TTS audio files
        for file_path in glob.glob(os.path.join(TEMP_AUDIO_DIR, "tts_audio_*.mp3")):
            try:
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
            except OSError:
                # If we can't remove the file, just continue
                continue
                
        # Clean up gradio cache directory as well
        from constants import GRADIO_CACHE_DIR, GRADIO_CLEAR_CACHE_OLDER_THAN
        
        if os.path.exists(GRADIO_CACHE_DIR):
            for file_path in glob.glob(os.path.join(GRADIO_CACHE_DIR, "*.mp3")):
                try:
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > GRADIO_CLEAR_CACHE_OLDER_THAN:
                            os.remove(file_path)
                except OSError:
                    continue
                    
    except Exception:
        # Don't let cleanup failures affect the main application
        pass

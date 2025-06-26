from google.cloud import texttospeech


# Local imports
from constants import (
    GOOGLE_CLOUD_API_KEY
)

# Initialize Google Cloud Text-to-Speech client
# Only initialize if API key is available
google_tts_client = None
if GOOGLE_CLOUD_API_KEY:
    google_tts_client = texttospeech.TextToSpeechClient(
        client_options={"api_key": GOOGLE_CLOUD_API_KEY}
    )

def list_voices():
    """Lists the available voices."""
    client = texttospeech.TextToSpeechClient(
        client_options={"api_key": GOOGLE_CLOUD_API_KEY}
    )

    # Performs the list voices request
    voices = client.list_voices()

    for voice in voices.voices:
        # Display the voice's name. Example: tpc-vocoded
        print(f"Name: {voice.name}")

        # Display the supported language codes for this voice. Example: "en-US"
        for language_code in voice.language_codes:
            print(f"Supported language: {language_code}")

        ssml_gender = texttospeech.SsmlVoiceGender(voice.ssml_gender)

        # Display the SSML Voice Gender
        print(f"SSML Voice Gender: {ssml_gender.name}")

        # Display the natural sample rate hertz for this voice. Example: 24000
        print(f"Natural Sample Rate Hertz: {voice.natural_sample_rate_hertz}\n")

list_voices()
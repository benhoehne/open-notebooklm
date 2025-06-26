"""
constants.py
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Key constants
APP_TITLE = "Pod GPT 🎙️"
CHARACTER_LIMIT = 150_000

# Gradio-related constants
GRADIO_CACHE_DIR = "./gradio_cached_examples/tmp/"
GRADIO_CLEAR_CACHE_OLDER_THAN = 1 * 24 * 60 * 60  # 1 day

# Temporary directory for audio files - ensure it's writable for non-admin users
TEMP_AUDIO_DIR = "./temp_audio/"

# Error messages-related constants
ERROR_MESSAGE_NO_INPUT = "Please provide at least one content source: upload PDF files, enter a website URL, or import a script file."
ERROR_MESSAGE_NOT_PDF = "The provided file is not a PDF. Please upload only PDF files."

ERROR_MESSAGE_READING_PDF = "Error reading the PDF file"
ERROR_MESSAGE_TOO_LONG = "The total content is too long. Please ensure the combined text from PDFs and URL is fewer than {CHARACTER_LIMIT} characters."

# Google Gemini API-related constants
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MAX_TOKENS = 65536
GEMINI_MODEL_ID = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.1

# Google Cloud Text-to-Speech API-related constants
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
GOOGLE_TTS_RETRY_ATTEMPTS = 3
GOOGLE_TTS_RETRY_DELAY = 5  # in seconds

# Enhanced voice configuration with multiple high-quality voices per gender/language
# Using ONLY Chirp HD and Chirp 3 HD voices - prioritizing Chirp HD where available

# Female voices - at least 2 per language, using only Chirp HD and Chirp 3 HD voices
FEMALE_VOICES = {
    "English": [
        "en-US-Chirp-HD-F",
        "en-US-Chirp-HD-O",
        "en-US-Chirp3-HD-Achernar",
        "en-US-Chirp3-HD-Aoede"
    ],
    "Spanish": [
        "es-ES-Chirp-HD-F",
        "es-ES-Chirp-HD-O",
        "es-ES-Chirp3-HD-Achernar",
        "es-ES-Chirp3-HD-Aoede"
    ],
    "French": [
        "fr-FR-Chirp-HD-F",
        "fr-FR-Chirp-HD-O",
        "fr-FR-Chirp3-HD-Achernar",
        "fr-FR-Chirp3-HD-Aoede"
    ],
    "German": [
        "de-DE-Chirp-HD-F",
        "de-DE-Chirp-HD-O", 
        "de-DE-Chirp3-HD-Achernar",
        "de-DE-Chirp3-HD-Aoede"
    ],
    "Italian": [
        "it-IT-Chirp-HD-F",
        "it-IT-Chirp-HD-O",
        "it-IT-Chirp3-HD-Achernar",
        "it-IT-Chirp3-HD-Aoede"
    ],
    "Portuguese": [
        "pt-BR-Chirp3-HD-Achernar", 
        "pt-BR-Chirp3-HD-Aoede",
        "pt-BR-Chirp3-HD-Callirrhoe",
        "pt-BR-Chirp3-HD-Despina"
    ],
    "Dutch": [
        "nl-NL-Chirp3-HD-Achernar",
        "nl-NL-Chirp3-HD-Aoede",
        "nl-NL-Chirp3-HD-Callirrhoe",
        "nl-NL-Chirp3-HD-Despina"
    ],
    "Polish": [
        "pl-PL-Chirp3-HD-Achernar",
        "pl-PL-Chirp3-HD-Aoede", 
        "pl-PL-Chirp3-HD-Callirrhoe",
        "pl-PL-Chirp3-HD-Despina"
    ],
    "Russian": [
        "ru-RU-Chirp3-HD-Achernar",
        "ru-RU-Chirp3-HD-Aoede",
        "ru-RU-Chirp3-HD-Callirrhoe",
        "ru-RU-Chirp3-HD-Despina"
    ],
    "Japanese": [
        "ja-JP-Chirp3-HD-Achernar",
        "ja-JP-Chirp3-HD-Aoede",
        "ja-JP-Chirp3-HD-Callirrhoe",
        "ja-JP-Chirp3-HD-Despina"
    ],
    "Korean": [
        "ko-KR-Chirp3-HD-Achernar",
        "ko-KR-Chirp3-HD-Aoede",
        "ko-KR-Chirp3-HD-Callirrhoe",
        "ko-KR-Chirp3-HD-Despina"
    ],
    "Chinese": [
        "cmn-CN-Chirp3-HD-Achernar",
        "cmn-CN-Chirp3-HD-Aoede", 
        "cmn-CN-Chirp3-HD-Callirrhoe",
        "cmn-CN-Chirp3-HD-Despina"
    ],
    "Hindi": [
        "hi-IN-Chirp3-HD-Achernar",
        "hi-IN-Chirp3-HD-Aoede",
        "hi-IN-Chirp3-HD-Callirrhoe",
        "hi-IN-Chirp3-HD-Despina"
    ],
    "Turkish": [
        "tr-TR-Chirp3-HD-Achernar",
        "tr-TR-Chirp3-HD-Aoede",
        "tr-TR-Chirp3-HD-Callirrhoe",
        "tr-TR-Chirp3-HD-Despina"
    ],
}

# Male voices - at least 2 per language, using only Chirp HD and Chirp 3 HD voices  
MALE_VOICES = {
    "English": [
        "en-US-Chirp-HD-D",
        "en-US-Chirp3-HD-Achird",
        "en-US-Chirp3-HD-Charon",
        "en-US-Chirp3-HD-Algenib"
    ],
    "Spanish": [
        "es-ES-Chirp-HD-D", 
        "es-ES-Chirp3-HD-Achird",
        "es-ES-Chirp3-HD-Charon",
        "es-ES-Chirp3-HD-Algenib"
    ],
    "French": [
        "fr-FR-Chirp-HD-D",
        "fr-FR-Chirp3-HD-Achird",
        "fr-FR-Chirp3-HD-Charon",
        "fr-FR-Chirp3-HD-Algenib"
    ],
    "German": [
        "de-DE-Chirp-HD-D", 
        "de-DE-Chirp3-HD-Achird",
        "de-DE-Chirp3-HD-Charon",
        "de-DE-Chirp3-HD-Algenib"
    ],
    "Italian": [
        "it-IT-Chirp-HD-D",
        "it-IT-Chirp3-HD-Achird",
        "it-IT-Chirp3-HD-Charon",
        "it-IT-Chirp3-HD-Algenib"
    ],
    "Portuguese": [
        "pt-BR-Chirp3-HD-Achird",
        "pt-BR-Chirp3-HD-Charon", 
        "pt-BR-Chirp3-HD-Algenib",
        "pt-BR-Chirp3-HD-Enceladus"
    ],
    "Dutch": [
        "nl-NL-Chirp3-HD-Achird",
        "nl-NL-Chirp3-HD-Charon",
        "nl-NL-Chirp3-HD-Algenib",
        "nl-NL-Chirp3-HD-Enceladus"
    ],
    "Polish": [
        "pl-PL-Chirp3-HD-Achird",
        "pl-PL-Chirp3-HD-Charon",
        "pl-PL-Chirp3-HD-Algenib",
        "pl-PL-Chirp3-HD-Enceladus"
    ],
    "Russian": [
        "ru-RU-Chirp3-HD-Achird",
        "ru-RU-Chirp3-HD-Charon",
        "ru-RU-Chirp3-HD-Algenib",
        "ru-RU-Chirp3-HD-Enceladus"
    ],
    "Japanese": [
        "ja-JP-Chirp3-HD-Achird",
        "ja-JP-Chirp3-HD-Charon",
        "ja-JP-Chirp3-HD-Algenib",
        "ja-JP-Chirp3-HD-Enceladus"
    ],
    "Korean": [
        "ko-KR-Chirp3-HD-Achird", 
        "ko-KR-Chirp3-HD-Charon",
        "ko-KR-Chirp3-HD-Algenib",
        "ko-KR-Chirp3-HD-Enceladus"
    ],
    "Chinese": [
        "cmn-CN-Chirp3-HD-Achird",
        "cmn-CN-Chirp3-HD-Charon",
        "cmn-CN-Chirp3-HD-Algenib",
        "cmn-CN-Chirp3-HD-Enceladus"
    ],
    "Hindi": [
        "hi-IN-Chirp3-HD-Achird",
        "hi-IN-Chirp3-HD-Charon", 
        "hi-IN-Chirp3-HD-Algenib",
        "hi-IN-Chirp3-HD-Enceladus"
    ],
    "Turkish": [
        "tr-TR-Chirp3-HD-Achird",
        "tr-TR-Chirp3-HD-Charon",
        "tr-TR-Chirp3-HD-Algenib",
        "tr-TR-Chirp3-HD-Enceladus"
    ],
}

def get_voice_assignments():
    """
    Randomly assign genders to host and guest roles for variety.
    This ensures we always have one male and one female voice, but the roles are mixed up.
    Now uses multiple voice options per gender for better variety.
    """
    import random
    
    # Randomly decide if host should be female (True) or male (False)
    host_is_female = random.choice([True, False])
    
    if host_is_female:
        return {
            "Host (Sam)": FEMALE_VOICES,
            "Guest": MALE_VOICES,
        }
    else:
        return {
            "Host (Sam)": MALE_VOICES,
            "Guest": FEMALE_VOICES,
        }

def get_custom_voice_assignments(host_gender: str = "random", guest_gender: str = "random"):
    """
    Assign genders to host and guest roles based on user preferences.
    Now supports multiple voice options per gender for better variety.
    
    Args:
        host_gender: "male", "female", or "random"
        guest_gender: "male", "female", or "random" 
    """
    import random
    
    # Handle host gender
    if host_gender == "male":
        host_voices = MALE_VOICES
    elif host_gender == "female":
        host_voices = FEMALE_VOICES
    else:  # random
        host_voices = random.choice([MALE_VOICES, FEMALE_VOICES])
    
    # Handle guest gender  
    if guest_gender == "male":
        guest_voices = MALE_VOICES
    elif guest_gender == "female":
        guest_voices = FEMALE_VOICES
    else:  # random
        guest_voices = random.choice([MALE_VOICES, FEMALE_VOICES])
    
    return {
        "Host (Sam)": host_voices,
        "Guest": guest_voices,
    }

def get_random_voice_for_language_and_gender(language: str, gender: str):
    """
    Get a random voice for a specific language and gender.
    
    Args:
        language: Language name (e.g., "English", "Spanish")
        gender: "male" or "female"
    
    Returns:
        str: Voice name (e.g., "en-US-Chirp3-HD-Achernar")
    """
    import random
    
    voices = FEMALE_VOICES if gender.lower() == "female" else MALE_VOICES
    
    if language in voices:
        return random.choice(voices[language])
    else:
        # Fallback to English if language not found
        return random.choice(voices["English"])

# Legacy variable for backwards compatibility - will be dynamically assigned
GOOGLE_TTS_VOICES = get_voice_assignments()

# Supported languages for Google Cloud TTS
SUPPORTED_LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese", 
    "Dutch", "Polish", "Russian", "Japanese", "Korean", "Chinese", 
    "Hindi", "Turkish"
]

# Jina Reader-related constants
JINA_READER_URL = "https://r.jina.ai/"
JINA_RETRY_ATTEMPTS = 3
JINA_RETRY_DELAY = 5  # in seconds

# UI-related constants
UI_DESCRIPTION = """
Generate Podcasts from PDFs using AI.

Built with:
- [Google Gemini Flash 🤖](https://ai.google.dev/gemini-api) for dialogue generation
- [Google Cloud Text-to-Speech 🎙️](https://cloud.google.com/text-to-speech) for high-quality voice synthesis
- [Jina Reader 🔍](https://jina.ai/reader/) for web content extraction

**Note:** Only the text is processed (100k character limits).
"""
UI_AVAILABLE_LANGUAGES = SUPPORTED_LANGUAGES
UI_INPUTS = {
    "file_upload": {
        "label": "1. 📄 Upload your PDF(s)",
        "file_types": [".pdf"],
        "file_count": "multiple",
    },
    "url": {
        "label": "2. 🔗 Paste a URL (optional)",
        "placeholder": "Enter a URL to include its content",
    },
    "question": {
        "label": "3. 🤔 Do you have a specific question or topic in mind?",
        "placeholder": "Enter a question or topic",
    },
    "tone": {
        "label": "4. 🎭 Choose the tone",
        "choices": ["Fun", "Formal", "Educational"],
        "value": "Fun",
    },
    "length": {
        "label": "5. ⏱️ Choose the length",
        "choices": ["Short (1-2 min)", "Medium (3-5 min)", "Long (10-12 min)"],
        "value": "Medium (3-5 min)",
    },
    "language": {
        "label": "6. 🌐 Choose the language",
        "choices": UI_AVAILABLE_LANGUAGES,
        "value": "English",
    },

}
UI_OUTPUTS = {
    "audio": {"label": "🔊 Podcast", "format": "mp3"},
    "transcript": {
        "label": "📜 Transcript",
    },
}
UI_API_NAME = "generate_podcast"
UI_ALLOW_FLAGGING = "never"
UI_CONCURRENCY_LIMIT = 1
UI_EXAMPLES = [
    [
        [str(Path("examples/1310.4546v1.pdf"))],
        "",
        "Explain this paper to me like I'm 5 years old",
        "Fun",
        "Short (1-2 min)",
        "English",
    ],
    [
        [],
        "https://en.wikipedia.org/wiki/Hugging_Face",
        "How did Hugging Face become so successful?",
        "Fun",
        "Short (1-2 min)",
        "English",
    ],
    [
        [],
        "https://simple.wikipedia.org/wiki/Taylor_Swift",
        "Why is Taylor Swift so popular?",
        "Fun",
        "Short (1-2 min)",
        "English",
    ],
]
UI_CACHE_EXAMPLES = False
UI_SHOW_API = True

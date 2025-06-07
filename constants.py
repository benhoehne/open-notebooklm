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
GEMINI_MODEL_ID = "gemini-2.5-flash-preview-05-20"
GEMINI_TEMPERATURE = 0.1

# Google Cloud Text-to-Speech API-related constants
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
GOOGLE_TTS_RETRY_ATTEMPTS = 3
GOOGLE_TTS_RETRY_DELAY = 5  # in seconds

# Voice configuration for different speakers using Chirp HD voices
# Chirp HD voices are the latest generation powered by LLMs, perfect for conversational applications

# Base voice mappings by gender and language
FEMALE_VOICES = {
    "English": "en-US-Chirp-HD-F",
    "Spanish": "es-ES-Chirp-HD-F", 
    "French": "fr-FR-Chirp-HD-F",
    "German": "de-DE-Chirp-HD-F",
    "Italian": "it-IT-Chirp-HD-F",
    "Portuguese": "pt-BR-Chirp-HD-F",
    "Dutch": "nl-NL-Chirp-HD-F",
    "Polish": "pl-PL-Chirp-HD-F",
    "Russian": "ru-RU-Chirp-HD-F",
    "Japanese": "ja-JP-Chirp-HD-F",
    "Korean": "ko-KR-Chirp-HD-F",
    "Chinese": "zh-CN-Chirp-HD-F",
    "Hindi": "hi-IN-Chirp-HD-F",
    "Turkish": "tr-TR-Chirp-HD-F",
}

MALE_VOICES = {
    "English": "en-US-Chirp-HD-D",
    "Spanish": "es-ES-Chirp-HD-D",
    "French": "fr-FR-Chirp-HD-D", 
    "German": "de-DE-Chirp-HD-D",
    "Italian": "it-IT-Chirp-HD-D",
    "Portuguese": "pt-BR-Chirp-HD-D",
    "Dutch": "nl-NL-Chirp-HD-D",
    "Polish": "pl-PL-Chirp-HD-D",
    "Russian": "ru-RU-Chirp-HD-D",
    "Japanese": "ja-JP-Chirp-HD-D",
    "Korean": "ko-KR-Chirp-HD-D",
    "Chinese": "zh-CN-Chirp-HD-D",
    "Hindi": "hi-IN-Chirp-HD-D",
    "Turkish": "tr-TR-Chirp-HD-D",
}

def get_voice_assignments():
    """
    Randomly assign genders to host and guest roles for variety.
    This ensures we always have one male and one female voice, but the roles are mixed up.
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

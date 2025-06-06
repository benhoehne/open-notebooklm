"""
constants.py
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Key constants
APP_TITLE = "Open NotebookLM 🎙️"
CHARACTER_LIMIT = 100_000

# Gradio-related constants
GRADIO_CACHE_DIR = "./gradio_cached_examples/tmp/"
GRADIO_CLEAR_CACHE_OLDER_THAN = 1 * 24 * 60 * 60  # 1 day

# Error messages-related constants
ERROR_MESSAGE_NO_INPUT = "Please provide at least one PDF file or a URL."
ERROR_MESSAGE_NOT_PDF = "The provided file is not a PDF. Please upload only PDF files."
ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS = "The selected language is not supported without advanced audio generation. Please enable advanced audio generation or choose a supported language."
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
GOOGLE_TTS_VOICES = {
    "Host (Jane)": {
        "English": "en-US-Chirp-HD-F",    # Female Chirp HD voice
        "Spanish": "es-ES-Chirp-HD-F",    # Female Chirp HD voice
        "French": "fr-FR-Chirp-HD-F",     # Female Chirp HD voice
        "German": "de-DE-Chirp-HD-F",     # Female Chirp HD voice
        "Italian": "it-IT-Chirp-HD-F",    # Female Chirp HD voice
        "Portuguese": "pt-BR-Chirp-HD-F", # Female Chirp HD voice
        "Japanese": "ja-JP-Chirp-HD-F",   # Female Chirp HD voice
        "Korean": "ko-KR-Chirp-HD-F",     # Female Chirp HD voice
        "Chinese": "zh-CN-Chirp-HD-F",    # Female Chirp HD voice
    },
    "Guest": {
        "English": "en-US-Chirp-HD-D",    # Male Chirp HD voice
        "Spanish": "es-ES-Chirp-HD-D",    # Male Chirp HD voice
        "French": "fr-FR-Chirp-HD-D",     # Male Chirp HD voice
        "German": "de-DE-Chirp-HD-D",     # Male Chirp HD voice
        "Italian": "it-IT-Chirp-HD-D",    # Male Chirp HD voice
        "Portuguese": "pt-BR-Chirp-HD-D", # Male Chirp HD voice
        "Japanese": "ja-JP-Chirp-HD-D",   # Male Chirp HD voice
        "Korean": "ko-KR-Chirp-HD-D",     # Male Chirp HD voice
        "Chinese": "zh-CN-Chirp-HD-D",    # Male Chirp HD voice
    }
}

# MeloTTS
MELO_API_NAME = "/synthesize"
MELO_TTS_SPACES_ID = "mrfakename/MeloTTS"
MELO_RETRY_ATTEMPTS = 3
MELO_RETRY_DELAY = 5  # in seconds

MELO_TTS_LANGUAGE_MAPPING = {
    "en": "EN",
    "es": "ES",
    "fr": "FR",
    "zh": "ZJ",
    "ja": "JP",
    "ko": "KR",
}


# Suno related constants
SUNO_LANGUAGE_MAPPING = {
    "English": "en",
    "Chinese": "zh",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Turkish": "tr",
}

# General audio-related constants
NOT_SUPPORTED_IN_MELO_TTS = list(
    set(SUNO_LANGUAGE_MAPPING.values()) - set(MELO_TTS_LANGUAGE_MAPPING.keys())
)
NOT_SUPPORTED_IN_MELO_TTS = [
    key for key, id in SUNO_LANGUAGE_MAPPING.items() if id in NOT_SUPPORTED_IN_MELO_TTS
]

# Jina Reader-related constants
JINA_READER_URL = "https://r.jina.ai/"
JINA_RETRY_ATTEMPTS = 3
JINA_RETRY_DELAY = 5  # in seconds

# UI-related constants
UI_DESCRIPTION = """
Generate Podcasts from PDFs using open-source AI.

Built with:
- [Google Gemini Flash 🤖](https://ai.google.dev/gemini-api) for dialogue generation
- [Google Cloud Text-to-Speech 🎙️](https://cloud.google.com/text-to-speech) for high-quality voice synthesis
- [Bark 🐶](https://huggingface.co/suno/bark) for advanced audio generation (experimental)
- [Jina Reader 🔍](https://jina.ai/reader/) for web content extraction

**Note:** Only the text is processed (100k character limits).
"""
UI_AVAILABLE_LANGUAGES = list(set(SUNO_LANGUAGE_MAPPING.keys()))
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
        "choices": ["Fun", "Formal"],
        "value": "Fun",
    },
    "length": {
        "label": "5. ⏱️ Choose the length",
        "choices": ["Short (1-2 min)", "Medium (3-5 min)"],
        "value": "Medium (3-5 min)",
    },
    "language": {
        "label": "6. 🌐 Choose the language",
        "choices": UI_AVAILABLE_LANGUAGES,
        "value": "English",
    },
    "advanced_audio": {
        "label": "7. 🔄 Use experimental Bark audio? (Slower, only if Google TTS unavailable)",
        "value": False,
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
        False,
    ],
    [
        [],
        "https://en.wikipedia.org/wiki/Hugging_Face",
        "How did Hugging Face become so successful?",
        "Fun",
        "Short (1-2 min)",
        "English",
        False,
    ],
    [
        [],
        "https://simple.wikipedia.org/wiki/Taylor_Swift",
        "Why is Taylor Swift so popular?",
        "Fun",
        "Short (1-2 min)",
        "English",
        False,
    ],
]
UI_CACHE_EXAMPLES = True
UI_SHOW_API = True

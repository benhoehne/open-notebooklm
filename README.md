# Open NotebookLM

## Overview

This project is inspired by the NotebookLM tool, and implements it with open-source LLMs and text-to-speech models. This tool processes the content of PDFs and web pages, generates a natural dialogue suitable for an audio podcast, and outputs it as an MP3 file.

Built with:
- [Google Gemini Flash 🤖](https://ai.google.dev/gemini-api) and [Instructor 📐](https://github.com/instructor-ai/instructor) 
- [Google Cloud Text-to-Speech 🎙️](https://cloud.google.com/text-to-speech) with Chirp HD voices
- [MeloTTS 🐚](https://huggingface.co/myshell-ai/MeloTTS-English) (fallback)
- [Bark 🐶](https://huggingface.co/suno/bark) (experimental)
- [Jina Reader 🔍](https://jina.ai/reader/)
- [Flask 🌐](https://flask.palletsprojects.com/) for the web interface
- [Tailwind CSS 🎨](https://tailwindcss.com/) for styling

## Features

- **Convert PDF to Podcast:** Upload multiple PDFs and convert their content into a podcast dialogue
- **Web Content Support:** Extract content from URLs to include in podcasts
- **Multiple Languages:** Support for 13 languages including English, Spanish, French, German, and more
- **Customizable Settings:** Choose tone (Fun, Formal, Educational), length, and language
- **High-Quality Audio:** Uses Google Cloud TTS with Chirp HD voices for natural-sounding speech
- **Professional Web Interface:** Clean, responsive Flask-based UI with Tailwind CSS styling
- **File Management:** Secure file upload handling and audio download capabilities

## Installation

To set up the project, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gabrielchua/open-notebooklm.git
   cd open-notebooklm
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Set up API Key(s):**
   For this project, we are using Google Gemini Flash with the new Google Gen AI SDK which supports structured output with pydantic objects. 
   
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a `.env` file in the project root and add: `GEMINI_API_KEY=your_api_key_here` (or `GOOGLE_API_KEY=your_api_key_here`)
   - Or set the environment variable: `export GEMINI_API_KEY=your_api_key_here` (or `export GOOGLE_API_KEY=your_api_key_here`)
   
   **Important:** We're using the new [Google Gen AI SDK](https://ai.google.dev/gemini-api/docs/libraries) (`google-genai`) which is the recommended library for accessing Gemini models. This new SDK provides structured output support with pydantic models and access to new features like multi-modal outputs.

2. **Run the application:**
   ```bash
   # Option 1: Use the convenience script
   ./run_flask.sh
   
   # Option 2: Manual steps
   npm run build-css-prod
   python flask_app.py
   ```
   This will launch a Flask web server at `http://127.0.0.1:5000`.

3. **Use the Application:**
   - Upload PDF documents or provide a website URL
   - Optionally specify a question or topic to focus on
   - Choose your preferred tone, length, and language
   - Click "Generate Podcast" to start the conversion process
   - Download the generated MP3 file and view the transcript

## Acknowledgements

This project is forked from [`knowsuchagency/pdf-to-podcast`](https://github.com/knowsuchagency/pdf-to-podcast)

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for more information.

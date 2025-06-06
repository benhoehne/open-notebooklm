---
title: Open NotebookLM
emoji: 🎙️
colorFrom: purple
colorTo: red
sdk: gradio
sdk_version: 5.0.1
app_file: app.py
pinned: true
header: mini
short_description: Personalised Podcasts For All - Available in 13 Languages
---

# Open NotebookLM

## Overview

This project is inspired by the NotebookLM tool, and implements it with open-source LLMs and text-to-speech models. This tool processes the content of a PDF, generates a natural dialogue suitable for an audio podcast, and outputs it as an MP3 file.

Built with:
- [Google Gemini Flash 🤖](https://ai.google.dev/gemini-api) and [Instructor 📐](https://github.com/instructor-ai/instructor) 
- [MeloTTS 🐚](https://huggingface.co/myshell-ai/MeloTTS-English)
- [Bark 🐶](https://huggingface.co/suno/bark)
- [Jina Reader 🔍](https://jina.ai/reader/)

## Features

- **Convert PDF to Podcast:** Upload a PDF and convert its content into a podcast dialogue.
- **Engaging Dialogue:** The generated dialogue is designed to be informative and entertaining.
- **User-friendly Interface:** Simple interface using Gradio for easy interaction.

## Installation

To set up the project, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gabrielchua/open-notebooklm.git
   cd open-notebooklm
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
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
   python app.py
   ```
   This will launch a Gradio interface in your web browser.

3. **Upload a PDF:**
   Upload the PDF document you want to convert into a podcast.

4. **Generate Audio:**
   Click the button to start the conversion process. The output will be an MP3 file containing the podcast dialogue.

## Acknowledgements

This project is forked from [`knowsuchagency/pdf-to-podcast`](https://github.com/knowsuchagency/pdf-to-podcast)

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for more information.

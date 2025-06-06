"""
Flask application for Open NotebookLM
"""

# Standard library imports
import os
import uuid
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from typing import List, Optional, Tuple
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Third-party imports
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from loguru import logger

# Import the existing podcast generation function and constants
from podcast_generator import generate_podcast as generate_podcast_core
from constants import (
    APP_TITLE,
    CHARACTER_LIMIT,
    ERROR_MESSAGE_NOT_PDF,
    ERROR_MESSAGE_NO_INPUT,
    ERROR_MESSAGE_NOT_SUPPORTED_IN_MELO_TTS,
    ERROR_MESSAGE_READING_PDF,
    ERROR_MESSAGE_TOO_LONG,
    UI_EXAMPLES,
)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'notebooklm-flask-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size

# Ensure upload and audio directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

# Configure logging
def setup_logging(app):
    """Set up logging configuration for the Flask app."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure Flask's built-in logger
    if not app.debug:
        # Production logging
        file_handler = RotatingFileHandler(
            'logs/notebooklm.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('NotebookLM Flask startup')
    else:
        # Development logging - log to both file and console
        file_handler = RotatingFileHandler(
            'logs/notebooklm_dev.log', 
            maxBytes=10240000, 
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('NotebookLM Flask development server startup')

# Set up logging
setup_logging(app)

def allowed_file(filename):
    """Check if the uploaded file is a PDF"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

@app.route('/')
def index():
    """Main page with the podcast generation form"""
    app.logger.info('Home page accessed')
    return render_template('index.html', 
                         title=APP_TITLE,
                         examples=UI_EXAMPLES)

@app.route('/generate', methods=['POST'])
def generate_podcast():
    """Handle podcast generation request"""
    start_time = datetime.now()
    app.logger.info('Podcast generation request started')
    
    try:
        # Debug: Log all form data and files
        app.logger.info(f'Form data received: {dict(request.form)}')
        app.logger.info(f'Files in request: {list(request.files.keys())}')
        
        # Handle file uploads
        uploaded_files = []
        if 'pdf_files' in request.files:
            files = request.files.getlist('pdf_files')
            app.logger.info(f'Number of files received: {len(files)}')
            
            for file in files:
                app.logger.info(f'Processing file: {file}, filename: {file.filename if file else "None"}')
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add unique prefix to avoid conflicts
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    uploaded_files.append(file_path)
                    app.logger.info(f'File uploaded: {filename} ({file.content_length} bytes)')
                elif file and file.filename:
                    app.logger.warning(f'Invalid file type: {file.filename}')
                    return render_template('index.html',
                                         error="Please upload only PDF files.",
                                         title=APP_TITLE,
                                         examples=UI_EXAMPLES)
                elif file:
                    app.logger.warning(f'File without filename: {file}')
        else:
            app.logger.warning('No pdf_files key found in request.files')

        # Get form data
        url = request.form.get('url', '').strip() or None
        question = request.form.get('question', '').strip() or None
        tone = request.form.get('tone', 'Fun')
        length = request.form.get('length', 'Medium (3-5 min)')
        language = request.form.get('language', 'English')
        use_advanced_audio = bool(request.form.get('use_advanced_audio'))

        # Log form data
        app.logger.info(f'Generation parameters: files={len(uploaded_files)}, url={bool(url)}, '
                       f'tone={tone}, length={length}, language={language}, advanced_audio={use_advanced_audio}')
        
        # Validate input
        if not uploaded_files and not url:
            app.logger.warning('No input provided (no files or URL)')
            return render_template('index.html',
                                 error=ERROR_MESSAGE_NO_INPUT,
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES)

        # Generate podcast using existing core function
        app.logger.info('Starting podcast generation...')
        audio_file_path, transcript = generate_podcast_core(
            files=uploaded_files,
            url=url,
            question=question,
            tone=tone,
            length=length,
            language=language,
            use_advanced_audio=use_advanced_audio
        )
        app.logger.info('Podcast generation completed successfully')

        # Move generated audio to static folder
        if audio_file_path:
            audio_filename = f"podcast_{uuid.uuid4().hex}.mp3"
            final_audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
            
            # Copy the file to static folder
            import shutil
            shutil.move(audio_file_path, final_audio_path)
            app.logger.info(f'Audio file saved: {audio_filename}')
        else:
            audio_filename = None
            app.logger.warning('No audio file generated')

        # Clean up uploaded files
        for file_path in uploaded_files:
            try:
                os.remove(file_path)
                app.logger.debug(f'Cleaned up uploaded file: {file_path}')
            except OSError as e:
                app.logger.warning(f'Failed to clean up file {file_path}: {e}')

        # Log completion time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        app.logger.info(f'Podcast generation completed in {duration:.2f} seconds')

        # Render success page with results
        return render_template('index.html',
                             audio_file=audio_filename,
                             transcript=transcript,
                             title=APP_TITLE,
                             examples=UI_EXAMPLES,
                             success="Podcast generated successfully!")

    except Exception as e:
        # Log the error with full traceback
        app.logger.error(f"Error generating podcast: {str(e)}", exc_info=True)
        
        # Clean up uploaded files on error
        for file_path in uploaded_files:
            try:
                os.remove(file_path)
                app.logger.debug(f'Cleaned up uploaded file after error: {file_path}')
            except OSError as cleanup_error:
                app.logger.warning(f'Failed to clean up file {file_path} after error: {cleanup_error}')
        
        # Log error completion time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        app.logger.error(f'Podcast generation failed after {duration:.2f} seconds')
        
        # Determine error message
        error_msg = str(e)
        if "Error" in error_msg:
            error_msg = error_msg.replace("Error: ", "")
        
        return render_template('index.html',
                             error=error_msg,
                             title=APP_TITLE,
                             examples=UI_EXAMPLES)

@app.route('/static/audio/<filename>')
def download_audio(filename):
    """Serve audio files"""
    app.logger.info(f'Audio file requested: {filename}')
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    app.logger.warning('File upload too large (413 error)')
    return render_template('index.html',
                         error="File too large! Maximum size is 16MB per file.",
                         title=APP_TITLE,
                         examples=UI_EXAMPLES), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    app.logger.warning(f'404 error: {request.url}')
    return render_template('index.html',
                         error="Page not found.",
                         title=APP_TITLE,
                         examples=UI_EXAMPLES), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    app.logger.error(f"Server error: {str(e)}", exc_info=True)
    return render_template('index.html',
                         error="An internal server error occurred. Please try again.",
                         title=APP_TITLE,
                         examples=UI_EXAMPLES), 500

if __name__ == '__main__':
    # Development server
    app.logger.info('Starting Flask development server on port 7000')
    app.run(debug=True, host='127.0.0.1', port=7000) 
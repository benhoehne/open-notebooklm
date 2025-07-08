"""
Flask application for Pod GPT with Authentication
"""

# Standard library imports
import os
import shutil
import uuid
import logging
import threading
import atexit
from pathlib import Path
from werkzeug.utils import secure_filename
from typing import List, Optional, Tuple
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Third-party imports
from flask import Flask, render_template, request, send_from_directory, after_this_request
from flask_login import LoginManager, login_required
from loguru import logger

# Import the existing podcast generation function and constants
from podcast_generator import generate_podcast as generate_podcast_core
from constants import (
    APP_TITLE,
    CHARACTER_LIMIT,
    ERROR_MESSAGE_NOT_PDF,
    ERROR_MESSAGE_NO_INPUT,
    ERROR_MESSAGE_READING_PDF,
    ERROR_MESSAGE_TOO_LONG,
    UI_EXAMPLES,
    TEMP_AUDIO_DIR,
    GRADIO_CACHE_DIR,
)

# Import authentication and models
from models import db, User
from auth import auth as auth_blueprint
from main import main as main_blueprint
from utils import cleanup_temp_audio_files

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'notebooklm-flask-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AUDIO_FOLDER'] = 'static/audio'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure upload and audio directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)  # Ensure temp audio directory exists

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)

# Create database tables
with app.app_context():
    db.create_all()

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

# Background cleanup scheduler
cleanup_scheduler = None

def start_background_cleanup():
    """Start background cleanup task that runs every hour"""
    global cleanup_scheduler
    
    def run_cleanup():
        try:
            app.logger.info('Running scheduled temp audio cleanup')
            cleanup_temp_audio_files()
            app.logger.info('Scheduled temp audio cleanup completed')
        except Exception as e:
            app.logger.error(f'Error during scheduled cleanup: {e}')
        
        # Schedule next cleanup in 1 hour (3600 seconds)
        global cleanup_scheduler
        cleanup_scheduler = threading.Timer(3600.0, run_cleanup)
        cleanup_scheduler.daemon = True
        cleanup_scheduler.start()
    
    # Start the first cleanup cycle
    cleanup_scheduler = threading.Timer(3600.0, run_cleanup)  # First run after 1 hour
    cleanup_scheduler.daemon = True
    cleanup_scheduler.start()
    app.logger.info('Background cleanup scheduler started (runs every hour)')

def stop_background_cleanup():
    """Stop background cleanup task"""
    global cleanup_scheduler
    if cleanup_scheduler:
        cleanup_scheduler.cancel()
        app.logger.info('Background cleanup scheduler stopped')

# Start background cleanup when app starts
start_background_cleanup()

# Ensure cleanup stops when app shuts down
atexit.register(stop_background_cleanup)

def allowed_file(filename):
    """Check if the uploaded file is a PDF"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

def allowed_script_file(filename):
    """Check if the uploaded file is a valid script file"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'md', 'txt'}

@app.route('/generate', methods=['POST'])
@login_required
def generate_podcast():
    """Handle podcast generation request"""
    start_time = datetime.now()
    app.logger.info('Podcast generation request started')
    
    # Clean up old temporary files to prevent disk space issues
    cleanup_temp_audio_files()
    
    try:
        # Debug: Log all form data and files
        app.logger.info(f'Form data received: {dict(request.form)}')
        app.logger.info(f'Files in request: {list(request.files.keys())}')
        
        # Handle script file upload first
        script_content = None
        if 'script_file' in request.files:
            script_file = request.files['script_file']
            app.logger.info(f'Script file found in request: {script_file}, filename: {script_file.filename if script_file else "None"}')
            if script_file and script_file.filename:
                app.logger.info(f'Script file has filename: {script_file.filename}')
                if allowed_script_file(script_file.filename):
                    app.logger.info(f'Script file type allowed: {script_file.filename}')
                    try:
                        script_content = script_file.read().decode('utf-8')
                        app.logger.info(f'Script content loaded: {len(script_content)} characters')
                        if script_content.strip():
                            app.logger.info(f'Script content is not empty: first 100 chars: {script_content[:100]}...')
                        else:
                            app.logger.warning('Script content is empty or whitespace only')
                            script_content = None  # Treat empty content as no content
                    except UnicodeDecodeError:
                        app.logger.error(f'Failed to decode script file: {script_file.filename}')
                        return render_template('index.html',
                                             error="Script file must be a valid text file (UTF-8 encoding).",
                                             title=APP_TITLE,
                                             examples=UI_EXAMPLES)
                else:
                    app.logger.warning(f'Invalid script file type: {script_file.filename}')
                    return render_template('index.html',
                                         error="Please upload only .md or .txt script files.",
                                         title=APP_TITLE,
                                         examples=UI_EXAMPLES)
            else:
                app.logger.info('Script file input exists but no file selected or no filename')
        else:
            app.logger.info('No script_file key found in request.files')
        
        # Handle PDF file uploads
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
        
        # Get new parameters for host/guest customization
        host_name = request.form.get('host_name', 'Sam').strip() or 'Sam'
        guest_name = request.form.get('guest_name', '').strip()
        host_gender = request.form.get('host_gender', 'random')
        guest_gender = request.form.get('guest_gender', 'random')

        # Log form data
        app.logger.info(f'Generation parameters: files={len(uploaded_files)}, url={bool(url)}, '
                       f'script_file={bool(script_content)}, tone={tone}, length={length}, language={language}, '
                       f'host_name={host_name}, guest_name={guest_name}, host_gender={host_gender}, guest_gender={guest_gender}')
        
        # Validate input - now including script_content
        if not uploaded_files and not url and not script_content:
            app.logger.warning('No input provided (no files, URL, or script)')
            return render_template('index.html',
                                 error=ERROR_MESSAGE_NO_INPUT,
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES)

        # If script content is provided, skip generation and go directly to audio synthesis
        if script_content:
            app.logger.info('Script content provided, skipping generation and synthesizing audio')
            
            # Log if other content sources were also provided but will be ignored
            if uploaded_files or url:
                app.logger.info(f'Ignoring {len(uploaded_files)} PDF files and URL ({bool(url)}) because script was provided')
            
            # Import the audio synthesis function
            from podcast_generator import synthesize_audio_from_script
            
            # Use provided guest name or extract from script
            final_guest_name = guest_name if guest_name else "AI Assistant"
            
            app.logger.info(f'Synthesizing audio with host: {host_name}, guest: {final_guest_name}, language: {language}')
            
            # Synthesize audio from provided script
            audio_file_path, transcript, vtt_file_path, h5p_file_path = synthesize_audio_from_script(
                script_content,
                language,
                host_name,
                final_guest_name,
                host_gender,
                guest_gender
            )
            
            app.logger.info('Audio synthesis from script completed successfully')
        else:
            # Generate podcast using existing core function
            app.logger.info('Starting podcast generation...')
            audio_file_path, transcript, vtt_file_path, h5p_file_path = generate_podcast_core(
                files=uploaded_files,
                url=url,
                question=question,
                tone=tone,
                length=length,
                language=language,
                host_name=host_name,
                guest_name=guest_name,
                host_gender=host_gender,
                guest_gender=guest_gender
            )
            app.logger.info('Podcast generation from content completed successfully')
        
        app.logger.info('Podcast generation completed successfully')

        # Move generated audio to static folder
        vtt_filename = None
        if audio_file_path:
            audio_filename = f"podcast_{uuid.uuid4().hex}.mp3"
            final_audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
            
            # Use a more robust approach for Synology systems
            try:
                # Copy the file first, then remove the original
                shutil.copy2(audio_file_path, final_audio_path)
                os.remove(audio_file_path)  # Clean up the original temp file
                app.logger.info(f'Audio file saved: {audio_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move audio file: {e}')
                # If copy fails, try to serve directly from temp location
                # Keep the original filename for fallback
                audio_filename = os.path.basename(audio_file_path)
                app.logger.warning(f'Serving audio directly from temp location: {audio_filename}')
        else:
            audio_filename = None
            app.logger.warning('No audio file generated')

        # Move VTT file to static folder
        if vtt_file_path and audio_filename:
            vtt_filename = audio_filename.replace('.mp3', '.vtt')
            final_vtt_path = os.path.join(app.config['AUDIO_FOLDER'], vtt_filename)
            
            try:
                shutil.copy2(vtt_file_path, final_vtt_path)
                os.remove(vtt_file_path)  # Clean up the original temp file
                app.logger.info(f'VTT file saved: {vtt_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move VTT file: {e}')
                vtt_filename = None

        # Move H5P file to static folder
        h5p_filename = None
        if h5p_file_path and audio_filename:
            h5p_filename = audio_filename.replace('.mp3', '.h5p')
            final_h5p_path = os.path.join(app.config['AUDIO_FOLDER'], h5p_filename)
            
            try:
                shutil.copy2(h5p_file_path, final_h5p_path)
                os.remove(h5p_file_path)  # Clean up the original temp file
                app.logger.info(f'H5P file saved: {h5p_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move H5P file: {e}')
                h5p_filename = None

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
        try:
            return render_template('index.html',
                                 audio_file=audio_filename,
                                 vtt_file=vtt_filename,
                                 h5p_file=h5p_filename,
                                 transcript=transcript,
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES,
                                 success="Podcast generated successfully!")
        except OSError as write_error:
            # Handle specific write errors that may occur on Synology systems
            app.logger.error(f'Write error during response: {write_error}')
            # Still try to return a basic response
            try:
                return render_template('index.html',
                                     audio_file=audio_filename,
                                     vtt_file=vtt_filename,
                                     transcript="Transcript may be unavailable due to system limitations.",
                                     title=APP_TITLE,
                                     examples=UI_EXAMPLES,
                                     success="Podcast generated successfully! (Note: Some display issues may occur on this system)")
            except:
                # Final fallback - minimal response
                return f"Podcast generated successfully! Audio file: {audio_filename}"

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

@app.route('/generate-script', methods=['POST'])
@login_required
def generate_script_only():
    """Generate script without audio synthesis for editing"""
    start_time = datetime.now()
    app.logger.info('Script generation request started')
    
    try:
        # Handle script file upload first
        script_content = None
        if 'script_file' in request.files:
            script_file = request.files['script_file']
            app.logger.info(f'Script file found in request: {script_file}, filename: {script_file.filename if script_file else "None"}')
            if script_file and script_file.filename:
                app.logger.info(f'Script file has filename: {script_file.filename}')
                if allowed_script_file(script_file.filename):
                    app.logger.info(f'Script file type allowed: {script_file.filename}')
                    try:
                        script_content = script_file.read().decode('utf-8')
                        app.logger.info(f'Script content loaded: {len(script_content)} characters')
                        if script_content.strip():
                            app.logger.info(f'Script content is not empty: first 100 chars: {script_content[:100]}...')
                        else:
                            app.logger.warning('Script content is empty or whitespace only')
                            script_content = None  # Treat empty content as no content
                    except UnicodeDecodeError:
                        app.logger.error(f'Failed to decode script file: {script_file.filename}')
                        return render_template('index.html',
                                             error="Script file must be a valid text file (UTF-8 encoding).",
                                             title=APP_TITLE,
                                             examples=UI_EXAMPLES)
                else:
                    app.logger.warning(f'Invalid script file type: {script_file.filename}')
                    return render_template('index.html',
                                         error="Please upload only .md or .txt script files.",
                                         title=APP_TITLE,
                                         examples=UI_EXAMPLES)
            else:
                app.logger.info('Script file input exists but no file selected or no filename')
        else:
            app.logger.info('No script_file key found in request.files')
        
        # Handle PDF file uploads (same as before)
        uploaded_files = []
        if 'pdf_files' in request.files:
            files = request.files.getlist('pdf_files')
            
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    uploaded_files.append(file_path)
                elif file and file.filename:
                    return render_template('index.html',
                                         error="Please upload only PDF files.",
                                         title=APP_TITLE,
                                         examples=UI_EXAMPLES)

        # Get form data
        url = request.form.get('url', '').strip() or None
        question = request.form.get('question', '').strip() or None
        tone = request.form.get('tone', 'Fun')
        length = request.form.get('length', 'Medium (3-5 min)')
        language = request.form.get('language', 'English')
        
        # Get host/guest customization
        host_name = request.form.get('host_name', 'Sam').strip() or 'Sam'
        guest_name = request.form.get('guest_name', '').strip()
        host_gender = request.form.get('host_gender', 'random')
        guest_gender = request.form.get('guest_gender', 'random')
        
        # If script content is provided, skip generation and go directly to editor
        if script_content:
            app.logger.info('Script content provided, opening in editor')
            
            # Create generation parameters for the editor
            import json
            generation_params = {
                'language': language,
                'host_name': host_name,
                'guest_name': guest_name if guest_name else "AI Assistant",
                'length': length,
                'host_gender': host_gender,
                'guest_gender': guest_gender
            }
            
            # Render script editor page with uploaded script
            return render_template('script_editor.html',
                                 script=script_content,
                                 generation_params=json.dumps(generation_params),
                                 title=APP_TITLE)
        
        # Validate input for script generation
        if not uploaded_files and not url:
            return render_template('index.html',
                                 error=ERROR_MESSAGE_NO_INPUT,
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES)

        # Import the script generation function
        from podcast_generator import generate_script_only as generate_script_core
        
        # Generate script only
        script, generation_params = generate_script_core(
            files=uploaded_files,
            url=url,
            question=question,
            tone=tone,
            length=length,
            language=language,
            host_name=host_name,
            guest_name=guest_name
        )
        
        # Clean up uploaded files
        for file_path in uploaded_files:
            try:
                os.remove(file_path)
            except OSError as e:
                app.logger.warning(f'Failed to clean up file {file_path}: {e}')

        # Store generation parameters in session for later use
        import json
        generation_params['host_gender'] = host_gender
        generation_params['guest_gender'] = guest_gender
        
        # Render script editor page
        return render_template('script_editor.html',
                             script=script,
                             generation_params=json.dumps(generation_params),
                             title=APP_TITLE)

    except Exception as e:
        app.logger.error(f"Error generating script: {str(e)}", exc_info=True)
        
        # Clean up uploaded files on error
        for file_path in uploaded_files:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        error_msg = str(e)
        if "Error" in error_msg:
            error_msg = error_msg.replace("Error: ", "")
        
        return render_template('index.html',
                             error=error_msg,
                             title=APP_TITLE,
                             examples=UI_EXAMPLES)

@app.route('/synthesize-audio', methods=['POST'])
@login_required
def synthesize_audio():
    """Synthesize audio from edited script"""
    start_time = datetime.now()
    app.logger.info('Audio synthesis request started')
    
    try:
        # Get the edited script and generation parameters
        edited_script = request.form.get('script', '').strip()
        generation_params_json = request.form.get('generation_params', '{}')
        
        if not edited_script:
            return render_template('index.html',
                                 error="No script provided for synthesis.",
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES)

        # Parse generation parameters
        import json
        generation_params = json.loads(generation_params_json)
        
        # Import the audio synthesis function
        from podcast_generator import synthesize_audio_from_script
        
        # Synthesize audio from edited script
        audio_file_path, transcript, vtt_file_path, h5p_file_path = synthesize_audio_from_script(
            edited_script,
            generation_params['language'],
            generation_params['host_name'],
            generation_params['guest_name'],
            generation_params['host_gender'],
            generation_params['guest_gender']
        )

        # Move generated audio to static folder
        vtt_filename = None
        if audio_file_path:
            audio_filename = f"podcast_{uuid.uuid4().hex}.mp3"
            final_audio_path = os.path.join(app.config['AUDIO_FOLDER'], audio_filename)
            
            # Use a more robust approach for Synology systems
            try:
                # Copy the file first, then remove the original
                shutil.copy2(audio_file_path, final_audio_path)
                os.remove(audio_file_path)  # Clean up the original temp file
                app.logger.info(f'Audio file saved: {audio_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move audio file: {e}')
                # If copy fails, try to serve directly from temp location
                # Keep the original filename for fallback
                audio_filename = os.path.basename(audio_file_path)
                app.logger.warning(f'Serving audio directly from temp location: {audio_filename}')
        else:
            audio_filename = None

        # Move VTT file to static folder
        if vtt_file_path and audio_filename:
            vtt_filename = audio_filename.replace('.mp3', '.vtt')
            final_vtt_path = os.path.join(app.config['AUDIO_FOLDER'], vtt_filename)
            
            try:
                shutil.copy2(vtt_file_path, final_vtt_path)
                os.remove(vtt_file_path)  # Clean up the original temp file
                app.logger.info(f'VTT file saved: {vtt_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move VTT file: {e}')
                vtt_filename = None

        # Move H5P file to static folder
        h5p_filename = None
        if h5p_file_path and audio_filename:
            h5p_filename = audio_filename.replace('.mp3', '.h5p')
            final_h5p_path = os.path.join(app.config['AUDIO_FOLDER'], h5p_filename)
            
            try:
                shutil.copy2(h5p_file_path, final_h5p_path)
                os.remove(h5p_file_path)  # Clean up the original temp file
                app.logger.info(f'H5P file saved: {h5p_filename}')
            except (PermissionError, OSError) as e:
                app.logger.error(f'Failed to move H5P file: {e}')
                h5p_filename = None

        # Log completion time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        app.logger.info(f'Audio synthesis completed in {duration:.2f} seconds')

        # Render success page with results
        try:
            return render_template('index.html',
                                 audio_file=audio_filename,
                                 vtt_file=vtt_filename,
                                 h5p_file=h5p_filename,
                                 transcript=transcript,
                                 title=APP_TITLE,
                                 examples=UI_EXAMPLES,
                                 success="Podcast synthesized successfully!")
        except OSError as write_error:
            # Handle specific write errors that may occur on Synology systems
            app.logger.error(f'Write error during response: {write_error}')
            # Still try to return a basic response
            try:
                return render_template('index.html',
                                     audio_file=audio_filename,
                                     vtt_file=vtt_filename,
                                     transcript="Transcript may be unavailable due to system limitations.",
                                     title=APP_TITLE,
                                     examples=UI_EXAMPLES,
                                     success="Podcast synthesized successfully! (Note: Some display issues may occur on this system)")
            except:
                # Final fallback - minimal response
                return f"Podcast synthesized successfully! Audio file: {audio_filename}"

    except Exception as e:
        app.logger.error(f"Error synthesizing audio: {str(e)}", exc_info=True)
        
        error_msg = str(e)
        if "Error" in error_msg:
            error_msg = error_msg.replace("Error: ", "")
        
        return render_template('index.html',
                             error=error_msg,
                             title=APP_TITLE,
                             examples=UI_EXAMPLES)

@app.route('/static/audio/<filename>')
def download_audio(filename):
    """Serve audio files - with fallback for Synology systems and post-download cleanup"""
    app.logger.info(f'Audio file requested: {filename}')
    
    def cleanup_after_download():
        """Clean up temporary files after download is complete"""
        try:
            app.logger.info('Running post-download temp audio cleanup')
            cleanup_temp_audio_files(max_age_hours=1)  # More aggressive cleanup after download
            app.logger.info('Post-download cleanup completed')
        except Exception as e:
            app.logger.error(f'Error during post-download cleanup: {e}')
    
    # Schedule cleanup to run after the response is sent
    @after_this_request
    def run_cleanup(response):
        # Use a separate thread to avoid blocking the response
        cleanup_thread = threading.Thread(target=cleanup_after_download)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        return response
    
    # First try serving from the configured audio folder
    static_audio_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
    if os.path.exists(static_audio_path):
        app.logger.info(f'Serving audio file from static folder: {filename}')
        return send_from_directory(app.config['AUDIO_FOLDER'], filename)
    
    # Fallback: try serving from gradio cache directory (temp location)
    temp_audio_path = os.path.join(GRADIO_CACHE_DIR, filename)
    if os.path.exists(temp_audio_path):
        app.logger.info(f'Serving audio file from temp location: {filename}')
        return send_from_directory(GRADIO_CACHE_DIR, filename)
    
    # Try serving from temp audio directory as well
    temp_audio_dir_path = os.path.join(TEMP_AUDIO_DIR, filename)
    if os.path.exists(temp_audio_dir_path):
        app.logger.info(f'Serving audio file from temp audio directory: {filename}')
        return send_from_directory(TEMP_AUDIO_DIR, filename)
    
    # If file not found in any location, return 404
    app.logger.error(f'Audio file not found in any location: {filename}')
    return render_template('index.html',
                         error="Audio file not found.",
                         title=APP_TITLE,
                         examples=UI_EXAMPLES), 404

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

@app.errorhandler(501)
def not_implemented(e):
    """Handle 501 errors - often related to permission issues on Synology"""
    app.logger.error(f"501 Not Implemented error: {str(e)}", exc_info=True)
    return render_template('index.html',
                          error="Service temporarily unavailable due to system permissions. Please ensure the application has write access to temporary directories, or contact your system administrator.",
                          title=APP_TITLE,
                          examples=UI_EXAMPLES), 501

if __name__ == '__main__':
    # Development server
    app.logger.info('Starting Flask development server on port 7000')
    app.run(debug=True, host='127.0.0.1', port=7000)

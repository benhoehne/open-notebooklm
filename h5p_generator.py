"""
H5P package generation module for creating H5P.Transcript packages.
"""

import json
import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from loguru import logger


def generate_h5p_package(
    audio_file_path: str,
    vtt_file_path: str,
    language: str = "en",
    title: str = "Podcast"
) -> str:
    """
    Generate an H5P package containing the audio file and VTT transcript.
    
    Args:
        audio_file_path: Path to the generated audio file
        vtt_file_path: Path to the generated VTT file
        language: Language code for the transcript (default: "en")
        title: Title for the H5P package (default: "Podcast")
    
    Returns:
        Path to the generated H5P package (ZIP file)
    """
    
    # Create a temporary directory for building the H5P package
    with tempfile.TemporaryDirectory() as temp_dir:
        h5p_dir = Path(temp_dir) / "h5p_package"
        
        # Copy the template structure
        template_dir = Path("transcript_template")
        shutil.copytree(template_dir, h5p_dir)
        
        # Generate unique IDs for the files
        audio_id = f"audio-{uuid.uuid4().hex[:8]}"
        vtt_id = f"file-{uuid.uuid4().hex[:8]}"
        subcontent_id = str(uuid.uuid4())
        
        # Copy audio file to the audios directory
        audio_filename = f"{audio_id}.mp3"
        audio_dest = h5p_dir / "content" / "audios" / audio_filename
        audio_dest.parent.mkdir(exist_ok=True)
        shutil.copy2(audio_file_path, audio_dest)
        
        # Copy VTT file to the content directory
        vtt_filename = f"{vtt_id}.vtt"
        vtt_dest = h5p_dir / "content" / vtt_filename
        shutil.copy2(vtt_file_path, vtt_dest)
        
        # Update h5p.json with the title
        h5p_json_path = h5p_dir / "h5p.json"
        with open(h5p_json_path, 'r', encoding='utf-8') as f:
            h5p_data = json.load(f)
        
        h5p_data["title"] = title
        h5p_data["extraTitle"] = title
        
        with open(h5p_json_path, 'w', encoding='utf-8') as f:
            json.dump(h5p_data, f, indent=2, ensure_ascii=False)
        
        # Update content.json with the file references
        content_json_path = h5p_dir / "content" / "content.json"
        
        content_data = {
            "mediumGroup": {
                "medium": {
                    "params": {
                        "playerMode": "minimalistic",
                        "fitToWrapper": False,
                        "controls": True,
                        "autoplay": False,
                        "playAudio": "Play audio",
                        "pauseAudio": "Pause audio",
                        "contentName": "Audio",
                        "audioNotSupported": "Your browser does not support this audio",
                        "files": [
                            {
                                "path": f"audios/{audio_filename}",
                                "mime": "audio/mpeg",
                                "copyright": {
                                    "license": "U"
                                }
                            }
                        ]
                    },
                    "library": "H5P.Audio 1.5",
                    "metadata": {
                        "contentType": "Audio",
                        "license": "U",
                        "title": "Untitled Audio",
                        "authors": [],
                        "changes": [],
                        "extraTitle": "Untitled Audio"
                    },
                    "subContentId": subcontent_id
                }
            },
            "transcriptFiles": [
                {
                    "label": language,
                    "languageCode": language,
                    "transcriptFile": {
                        "path": vtt_filename,
                        "mime": "text/vtt",
                        "copyright": {
                            "license": "U"
                        }
                    }
                }
            ],
            "behaviour": {
                "maxLines": 10,
                "showOnLoad": True
            },
            "chapters": {
                "useIVBookmarks": False
            },
            "l10n": {
                "noMedium": "No medium was assigned to the transcript.",
                "noTranscript": "No transcript was provided.",
                "troubleWebVTT": "There seems to be something wrong with the WebVTT file. Please consult the browser's development console for more information.",
                "chapterMarks": "Chapter marks",
                "unnamedOption": "Unnamed option"
            },
            "a11y": {
                "buttonVisible": "Hide transcript. Currently visible.",
                "buttonInvisible": "Show transcript. Currently not visible.",
                "buttonAutoscrollActive": "Turn off autoscroll. Currently active.",
                "buttonAutoscrollInactive": "Turn on autoscroll. Currently not active.",
                "buttonAutoscrollDisabled": "Autoscroll option disabled.",
                "buttonInteractive": "Switch to plaintext view",
                "buttonPlaintext": "Switch to interactive transcript view.",
                "buttonModeDisabled": "Mode switching disabled.",
                "buttonTimeActive": "Hide start time. Currently shown.",
                "buttonTimeInactive": "Show start time. Currently not shown.",
                "buttonTimeDisabled": "Start time option disabled.",
                "buttonLineBreakActive": "Hide line breaks. Currently shown.",
                "buttonLineBreakInactive": "Show line breaks. Currently not shown.",
                "buttonLineBreakDisabled": "Line break option disabled.",
                "buttonChapterMarksOpen": "Open chapter marks",
                "buttonChapterMarksClose": "Close chapter marks",
                "buttonChapterMarksDisabled": "Chapter marks disabled.",
                "interactiveTranscript": "Interactive transcript",
                "selectField": "Select what transcript to display.",
                "selectFieldDisabled": "Select field disabled.",
                "enterToHighlight": "Enter a query to highlight relevant text.",
                "searchboxDisabled": "Search box disabled.",
                "close": "Close"
            }
        }
        
        with open(content_json_path, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False)
        
        # Create the H5P package (ZIP file)
        from constants import GRADIO_CACHE_DIR
        
        # Ensure the cache directory exists
        os.makedirs(GRADIO_CACHE_DIR, exist_ok=True)
        
        # Generate unique filename for the H5P package
        h5p_filename = f"podcast_{uuid.uuid4().hex}.h5p"
        h5p_path = os.path.join(GRADIO_CACHE_DIR, h5p_filename)
        
        # Create ZIP file
        with zipfile.ZipFile(h5p_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(h5p_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, h5p_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Generated H5P package: {h5p_path}")
        return h5p_path

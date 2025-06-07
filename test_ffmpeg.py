#!/usr/bin/env python3
"""
Simple test script to check FFmpeg availability for pydub
"""

import subprocess
import sys
from pathlib import Path

def test_system_ffmpeg():
    """Test if system FFmpeg is available"""
    print("=== Testing System FFmpeg ===")
    
    # Test ffmpeg
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ffmpeg found at: {result.stdout.strip()}")
        else:
            print("❌ ffmpeg not found in PATH")
    except Exception as e:
        print(f"❌ Error checking ffmpeg: {e}")
    
    # Test ffprobe
    try:
        result = subprocess.run(['which', 'ffprobe'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ffprobe found at: {result.stdout.strip()}")
        else:
            print("❌ ffprobe not found in PATH")
    except Exception as e:
        print(f"❌ Error checking ffprobe: {e}")

def test_pydub_ffmpeg():
    """Test if pydub can find FFmpeg"""
    print("\n=== Testing pydub FFmpeg Integration ===")
    
    try:
        from pydub import AudioSegment
        from pydub.utils import which
        
        # Check what pydub thinks about ffmpeg
        ffmpeg_path = which("ffmpeg")
        ffprobe_path = which("ffprobe")
        
        print(f"pydub ffmpeg path: {ffmpeg_path}")
        print(f"pydub ffprobe path: {ffprobe_path}")
        
        if ffmpeg_path and ffprobe_path:
            print("✅ pydub can find both ffmpeg and ffprobe")
        else:
            print("❌ pydub cannot find FFmpeg tools")
            
    except ImportError as e:
        print(f"❌ Cannot import pydub: {e}")
    except Exception as e:
        print(f"❌ Error testing pydub: {e}")

def test_audio_conversion():
    """Test actual audio conversion"""
    print("\n=== Testing Audio Conversion ===")
    
    try:
        from pydub import AudioSegment
        
        # Create a simple 1-second sine wave as test
        print("Attempting to create a test audio segment...")
        
        # This will test if pydub can work with FFmpeg
        test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        print("✅ Successfully created test audio segment")
        
        # Test export (this is where FFmpeg is typically needed)
        test_file = "/tmp/test_audio.mp3"
        test_audio.export(test_file, format="mp3")
        print(f"✅ Successfully exported audio to {test_file}")
        
        # Clean up
        Path(test_file).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Audio conversion test failed: {e}")

if __name__ == "__main__":
    print("FFmpeg Availability Test")
    print("=" * 40)
    
    test_system_ffmpeg()
    test_pydub_ffmpeg()
    test_audio_conversion()
    
    print("\n" + "=" * 40)
    print("Test completed!") 
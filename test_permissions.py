#!/usr/bin/env python3
"""
Test script to verify permission fixes for Synology NAS systems.
This script tests the key operations that may fail with non-admin users.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

def test_directory_creation():
    """Test creating directories with proper permissions."""
    print("Testing directory creation...")
    
    test_dirs = [
        "./gradio_cached_examples/tmp/",
        "./temp_audio/",
        "./static/audio/",
        "./uploads/"
    ]
    
    for dir_path in test_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Successfully created directory: {dir_path}")
        except PermissionError as e:
            print(f"❌ Permission denied creating directory {dir_path}: {e}")
        except Exception as e:
            print(f"❌ Error creating directory {dir_path}: {e}")

def test_temp_file_operations():
    """Test temporary file creation and manipulation."""
    print("\nTesting temporary file operations...")
    
    # Test 1: Create temp file in custom directory
    try:
        os.makedirs("./temp_audio/", exist_ok=True)
        unique_filename = f"test_audio_{uuid.uuid4().hex}.mp3"
        temp_file_path = os.path.join("./temp_audio/", unique_filename)
        
        with open(temp_file_path, 'wb') as f:
            f.write(b"test audio content")
        
        print(f"✅ Successfully created temp file: {temp_file_path}")
        
        # Clean up
        os.remove(temp_file_path)
        print(f"✅ Successfully removed temp file: {temp_file_path}")
        
    except PermissionError as e:
        print(f"❌ Permission denied with temp file operations: {e}")
    except Exception as e:
        print(f"❌ Error with temp file operations: {e}")

def test_file_copy_operations():
    """Test file copy operations between directories."""
    print("\nTesting file copy operations...")
    
    try:
        # Create source file
        os.makedirs("./gradio_cached_examples/tmp/", exist_ok=True)
        os.makedirs("./static/audio/", exist_ok=True)
        
        source_file = "./gradio_cached_examples/tmp/test_source.mp3"
        dest_file = "./static/audio/test_dest.mp3"
        
        # Create source file
        with open(source_file, 'wb') as f:
            f.write(b"test audio content for copy")
        
        # Test copy operation
        shutil.copy2(source_file, dest_file)
        print(f"✅ Successfully copied file from {source_file} to {dest_file}")
        
        # Clean up
        os.remove(source_file)
        os.remove(dest_file)
        print(f"✅ Successfully cleaned up test files")
        
    except PermissionError as e:
        print(f"❌ Permission denied with file copy operations: {e}")
    except Exception as e:
        print(f"❌ Error with file copy operations: {e}")

def test_fallback_file_serving():
    """Test file serving from different locations."""
    print("\nTesting file serving fallback...")
    
    try:
        # Create test files in both locations
        os.makedirs("./static/audio/", exist_ok=True)
        os.makedirs("./gradio_cached_examples/tmp/", exist_ok=True)
        
        static_file = "./static/audio/test_static.mp3"
        temp_file = "./gradio_cached_examples/tmp/test_temp.mp3"
        
        with open(static_file, 'wb') as f:
            f.write(b"static audio content")
        
        with open(temp_file, 'wb') as f:
            f.write(b"temp audio content")
        
        # Test file existence checks
        if os.path.exists(static_file):
            print(f"✅ Static file exists and is accessible: {static_file}")
        
        if os.path.exists(temp_file):
            print(f"✅ Temp file exists and is accessible: {temp_file}")
        
        # Clean up
        os.remove(static_file)
        os.remove(temp_file)
        print(f"✅ Successfully cleaned up test files")
        
    except Exception as e:
        print(f"❌ Error with file serving test: {e}")

def main():
    """Run all permission tests."""
    print("🔍 Running Synology NAS permission tests...")
    print("=" * 50)
    
    test_directory_creation()
    test_temp_file_operations()
    test_file_copy_operations()
    test_fallback_file_serving()
    
    print("\n" + "=" * 50)
    print("✨ Permission tests completed!")
    print("\nIf all tests passed, the podcast generator should work properly")
    print("on your Synology NAS system with a non-admin user account.")

if __name__ == "__main__":
    main() 
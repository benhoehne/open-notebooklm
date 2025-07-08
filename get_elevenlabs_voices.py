"""
Script to fetch available ElevenLabs voices and categorize them by gender and language.
This will help us populate the constants.py file with ElevenLabs voice options.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_elevenlabs_voices():
    """Fetch all available ElevenLabs voices."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY not found in environment variables")
        return None
    
    url = "https://api.elevenlabs.io/v2/voices"
    headers = {
        "xi-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        voices = data.get("voices", [])
        print(f"Found {len(voices)} voices")
        
        # Categorize voices by gender and language
        male_voices = {}
        female_voices = {}
        
        for voice in voices:
            voice_id = voice.get("voice_id")
            name = voice.get("name")
            category = voice.get("category", "unknown")
            labels = voice.get("labels", {})
            
            # Skip if this is not a default/premade voice (to avoid user-generated content)
            if category not in ["premade", "generated"]:
                continue
            
            # Try to determine gender from labels or name
            gender = labels.get("gender", "").lower()
            if not gender:
                # Try to infer from name or other indicators
                if any(indicator in name.lower() for indicator in ["male", "man", "boy", "masculine"]):
                    gender = "male"
                elif any(indicator in name.lower() for indicator in ["female", "woman", "girl", "feminine"]):
                    gender = "female"
                else:
                    # Skip voices where we can't determine gender
                    continue
            
            # Get language info
            verified_languages = voice.get("verified_languages", [])
            if not verified_languages:
                # Default to English if no language specified
                languages = ["English"]
            else:
                languages = [lang.get("language", "English") for lang in verified_languages]
            
            voice_info = {
                "voice_id": voice_id,
                "name": name,
                "languages": languages
            }
            
            # Add to appropriate gender category
            if gender == "male":
                for lang in languages:
                    if lang not in male_voices:
                        male_voices[lang] = []
                    male_voices[lang].append(voice_info)
            elif gender == "female":
                for lang in languages:
                    if lang not in female_voices:
                        female_voices[lang] = []
                    female_voices[lang].append(voice_info)
        
        return {
            "male_voices": male_voices,
            "female_voices": female_voices
        }
        
    except requests.RequestException as e:
        print(f"Error fetching ElevenLabs voices: {e}")
        return None

if __name__ == "__main__":
    voices = get_elevenlabs_voices()
    if voices:
        print("\n=== MALE VOICES ===")
        for lang, voice_list in voices["male_voices"].items():
            print(f"\n{lang}:")
            for voice in voice_list[:4]:  # Limit to 4 voices per language
                print(f"  - {voice['name']} ({voice['voice_id']})")
        
        print("\n=== FEMALE VOICES ===")
        for lang, voice_list in voices["female_voices"].items():
            print(f"\n{lang}:")
            for voice in voice_list[:4]:  # Limit to 4 voices per language
                print(f"  - {voice['name']} ({voice['voice_id']})")

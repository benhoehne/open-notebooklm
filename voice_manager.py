"""
voice_manager.py
Voice management utilities for loading and managing voice configurations
"""

import json
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class VoiceManager:
    """Manages voice configurations for different TTS providers"""
    
    def __init__(self):
        self.voices_dir = Path("voices")
        self._voice_cache = {}
    
    def load_voices(self, provider: str, language: str) -> List[Dict]:
        """
        Load voices for a specific provider and language.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name (e.g., "English", "Spanish")
            
        Returns:
            List of voice dictionaries with id, name, and gender
        """
        cache_key = f"{provider}_{language}"
        
        if cache_key in self._voice_cache:
            return self._voice_cache[cache_key]
        
        voice_file = self.voices_dir / provider / f"{language.lower()}.json"
        
        if not voice_file.exists():
            print(f"Warning: Voice file not found: {voice_file}")
            return []
        
        try:
            with open(voice_file, 'r') as f:
                data = json.load(f)
                voices = data.get('voices', [])
                self._voice_cache[cache_key] = voices
                return voices
        except Exception as e:
            print(f"Error loading voices from {voice_file}: {e}")
            return []
    
    def get_voices_by_gender(self, provider: str, language: str, gender: str) -> List[Dict]:
        """
        Get voices filtered by gender.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name
            gender: "male" or "female"
            
        Returns:
            List of voice dictionaries matching the gender
        """
        voices = self.load_voices(provider, language)
        return [voice for voice in voices if voice.get('gender', '').lower() == gender.lower()]
    
    def get_random_voice(self, provider: str, language: str, gender: str) -> Optional[Dict]:
        """
        Get a random voice for the specified criteria.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name
            gender: "male", "female", or "random"
            
        Returns:
            Random voice dictionary or None if no voices found
        """
        if gender == "random":
            # Choose a random gender first
            gender = random.choice(["male", "female"])
        
        voices = self.get_voices_by_gender(provider, language, gender)
        return random.choice(voices) if voices else None
    
    def get_voice_by_id(self, provider: str, language: str, voice_id: str) -> Optional[Dict]:
        """
        Get a specific voice by its ID.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name
            voice_id: Voice ID to find
            
        Returns:
            Voice dictionary or None if not found
        """
        voices = self.load_voices(provider, language)
        for voice in voices:
            if voice.get('id') == voice_id:
                return voice
        return None
    
    def get_available_languages(self, provider: str) -> List[str]:
        """
        Get list of available languages for a provider.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            
        Returns:
            List of language names
        """
        provider_dir = self.voices_dir / provider
        if not provider_dir.exists():
            return []
        
        languages = []
        for file_path in provider_dir.glob("*.json"):
            language = file_path.stem.capitalize()
            languages.append(language)
        
        return sorted(languages)
    
    def get_voice_assignments(self, provider: str, language: str, host_gender: str = "random", guest_gender: str = "random") -> Dict[str, Dict]:
        """
        Get voice assignments for host and guest.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name
            host_gender: "male", "female", or "random"
            guest_gender: "male", "female", or "random"
            
        Returns:
            Dictionary with host and guest voice assignments
        """
        # Handle random gender assignment
        if host_gender == "random":
            host_gender = random.choice(["male", "female"])
        
        if guest_gender == "random":
            guest_gender = random.choice(["male", "female"])
        
        # Get voices for each role
        host_voice = self.get_random_voice(provider, language, host_gender)
        guest_voice = self.get_random_voice(provider, language, guest_gender)
        
        return {
            "host": host_voice,
            "guest": guest_voice
        }
    
    def get_voice_options_for_language(self, provider: str, language: str) -> Dict[str, List[Dict]]:
        """
        Get all voice options for a language, organized by gender.
        
        Args:
            provider: "google_tts" or "elevenlabs"
            language: Language name
            
        Returns:
            Dictionary with 'male' and 'female' keys containing voice lists
        """
        voices = self.load_voices(provider, language)
        
        male_voices = [v for v in voices if v.get('gender', '').lower() == 'male']
        female_voices = [v for v in voices if v.get('gender', '').lower() == 'female']
        
        return {
            "male": male_voices,
            "female": female_voices
        }

# Global voice manager instance
voice_manager = VoiceManager()

# Convenience functions for backward compatibility
def load_voices(provider: str, language: str) -> List[Dict]:
    """Load voices for a specific provider and language"""
    return voice_manager.load_voices(provider, language)

def get_voices_by_gender(provider: str, language: str, gender: str) -> List[Dict]:
    """Get voices filtered by gender"""
    return voice_manager.get_voices_by_gender(provider, language, gender)

def get_random_voice(provider: str, language: str, gender: str) -> Optional[Dict]:
    """Get a random voice for the specified criteria (gender can be 'male', 'female', or 'random')"""
    return voice_manager.get_random_voice(provider, language, gender)

def get_voice_by_id(provider: str, language: str, voice_id: str) -> Optional[Dict]:
    """Get a specific voice by its ID"""
    return voice_manager.get_voice_by_id(provider, language, voice_id)

def get_voice_assignments(provider: str, language: str, host_gender: str = "random", guest_gender: str = "random") -> Dict[str, Dict]:
    """Get voice assignments for host and guest"""
    return voice_manager.get_voice_assignments(provider, language, host_gender, guest_gender)

def get_voice_options_for_language(provider: str, language: str) -> Dict[str, List[Dict]]:
    """Get all voice options for a language, organized by gender"""
    return voice_manager.get_voice_options_for_language(provider, language) 
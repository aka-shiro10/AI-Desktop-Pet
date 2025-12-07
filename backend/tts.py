"""
Kokoro Text-to-Speech Module
Lightweight, natural-sounding TTS with emotion/style control.
"""

import io
import base64
import numpy as np

try:
    from kokoro import KPipeline
    import soundfile as sf
except ImportError:
    raise ImportError("Required packages not found. Install with: pip install kokoro soundfile")


class KokoroTTS:
    """Wrapper for Kokoro TTS with female voice options and emotion support."""
    
    def __init__(self, lang_code='a', voice='af_heart'):
        """
        Initialize Kokoro TTS.
        
        Args:
            lang_code (str): Language code ('a' for English, 'ja' for Japanese, etc.)
            voice (str): Voice style. Female options: 'af_heart', 'af_bella', 'af_sarah', 'af_Nicole'
        """
        self.lang_code = lang_code
        self.voice = voice
        self.pipeline = None
        self._initialize_pipeline()
        
        # Female voice options with descriptions
        self.female_voices = {
            'af_heart': 'Warm, emotional, friendly female',
            'af_bella': 'Warm, expressive female',
            'af_sarah': 'Natural, conversational female',
            'af_Nicole': 'Clear, professional female',
        }
    
    def _initialize_pipeline(self):
        """Initialize Kokoro pipeline (lazy loading)."""
        if self.pipeline is None:
            print(f"Loading Kokoro TTS model (lang: {self.lang_code}, voice: {self.voice})...")
            self.pipeline = KPipeline(lang_code=self.lang_code)
            print(f"✓ Kokoro TTS loaded successfully")
    
    def synthesize(self, text, voice=None, speed=1.0):
        """
        Synthesize text to speech.
        
        Args:
            text (str): Text to synthesize
            voice (str): Voice style (uses self.voice if None)
            speed (float): Speech speed (1.0 = normal)
        
        Returns:
            tuple: (audio_bytes, sample_rate)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        voice = voice or self.voice
        
        try:
            # Generate speech
            generator = self.pipeline(text, voice=voice)
            
            audio_frames = []
            for gs, ps, audio in generator:
                audio_frames.append(audio)
            
            # Concatenate all frames
            if audio_frames:
                audio = np.concatenate(audio_frames)
            else:
                raise RuntimeError("No audio generated")
            
            # Apply speed adjustment if needed
            if speed != 1.0:
                audio = self._adjust_speed(audio, speed)
            
            return audio, 24000  # Kokoro outputs at 24kHz
        
        except Exception as e:
            raise RuntimeError(f"Kokoro synthesis failed: {str(e)}")
    
    def synthesize_to_wav(self, text, output_path, voice=None, speed=1.0):
        """
        Synthesize text and save to WAV file.
        
        Args:
            text (str): Text to synthesize
            output_path (str): Path to save WAV file
            voice (str): Voice style
            speed (float): Speech speed
        """
        audio, sample_rate = self.synthesize(text, voice=voice, speed=speed)
        sf.write(output_path, audio, sample_rate)
        print(f"✓ Saved to {output_path}")
    
    def synthesize_to_base64(self, text, voice=None, speed=1.0):
        """
        Synthesize text and return as base64-encoded WAV.
        
        Args:
            text (str): Text to synthesize
            voice (str): Voice style
            speed (float): Speech speed
        
        Returns:
            str: Base64-encoded audio
        """
        audio, sample_rate = self.synthesize(text, voice=voice, speed=speed)
        
        # Save to bytes buffer with format specification
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.getvalue()
        
        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        return audio_b64
    
    def set_voice(self, voice):
        """Change voice style."""
        if voice not in self.female_voices:
            print(f"⚠ Warning: '{voice}' not in known female voices")
        self.voice = voice
        print(f"✓ Voice set to '{voice}'")
    
    def list_female_voices(self):
        """List available female voice options."""
        print("Available female voices:")
        for voice_id, description in self.female_voices.items():
            print(f"  - {voice_id}: {description}")
    
    @staticmethod
    def _adjust_speed(audio, speed):
        """Adjust audio playback speed without changing pitch."""
        if speed == 1.0:
            return audio
        
        # Simple speed adjustment via resampling
        new_length = int(len(audio) / speed)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio)


# Global TTS instance for FastAPI integration
_tts_instance = None


def get_tts_instance(lang_code='a', voice='af_heart'):
    """Get or create Kokoro TTS instance (singleton)."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = KokoroTTS(lang_code=lang_code, voice=voice)
    return _tts_instance


if __name__ == "__main__":
    # Test Kokoro TTS
    tts = KokoroTTS(voice='af_heart')
    tts.list_female_voices()
    
    # Test synthesis
    test_text = "A quick brown fox had sex with the lazy dog"
    audio, sr = tts.synthesize(test_text)
    print(f"Generated {len(audio)} samples at {sr}Hz")
    
    # Save test file
    tts.synthesize_to_wav(test_text, "test_kokoro_output.wav")

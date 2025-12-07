import os
import tempfile

import numpy as np
import torch
import scipy.io.wavfile as wavfile
import scipy.signal as sps
import whisper

# Load Whisper once (tiny model is fast and lightweight)
model = whisper.load_model("tiny")


def _load_audio_no_ffmpeg(path: str) -> np.ndarray:
    """Load WAV without ffmpeg/torchaudio; return mono 16 kHz float32 numpy array."""
    sr, data = wavfile.read(path)

    # Convert to float32 and normalize to [-1, 1]
    if np.issubdtype(data.dtype, np.integer):
        max_int = np.iinfo(data.dtype).max
        data = data.astype(np.float32) / max_int
    else:
        data = data.astype(np.float32)
        peak = np.max(np.abs(data)) if data.size else 1.0
        if peak > 0:
            data /= peak

    # If stereo/multi-channel, average to mono
    if data.ndim > 1:
        data = data.mean(axis=1)

    # Resample to 16 kHz if needed
    target_sr = 16000
    if sr != target_sr:
        new_len = int(len(data) * target_sr / sr)
        data = sps.resample(data, new_len)
        sr = target_sr

    return data


def transcribe_wav(file_bytes: bytes) -> str:
    """Convert WAV bytes → text, without needing ffmpeg."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        f.write(file_bytes)
        temp_path = f.name

    try:
        audio = _load_audio_no_ffmpeg(temp_path)
        result = model.transcribe(audio, fp16=False, language="en")
        return result.get("text", "").strip()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass




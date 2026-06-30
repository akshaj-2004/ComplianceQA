import whisper

_whisper_model = None


def get_whisper_model():
    """Lazily loads and caches the Whisper model.
    
    The model is loaded on first call and reused afterwards.
    This avoids blocking the entire module import with a heavy model load.
    """
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model

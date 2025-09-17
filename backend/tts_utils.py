def generate_tts_file(text: str, lang: str = "en"):
    """
    Generates MP3 with gTTS, returns (file_path, public_url).
    """
    filename = f"tts_{uuid4().hex}.mp3"
    filepath = os.path.join(TTS_DIR, filename)

    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filepath)

    if not BASE_URL:
        public_url = f"/static/tts/{filename}"
    else:
        public_url = f"{BASE_URL.rstrip('/')}/static/tts/{filename}"

    return filepath, public_url

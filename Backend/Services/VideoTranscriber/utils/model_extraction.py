from faster_whisper import WhisperModel

# Force model download
model = WhisperModel("base", download_root=None)
print("Model downloaded successfully.")

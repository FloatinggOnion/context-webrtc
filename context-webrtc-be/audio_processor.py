import os
from pydub import AudioSegment

def process_audio(file_path: str):
    """Process the uploaded audio file."""
    # Example: Convert to MP3 or analyze the audio
    audio = AudioSegment.from_file(file_path)
    print(f"Audio duration: {len(audio)} ms")

    # Save the processed audio (optional)
    output_path = file_path.replace(".wav", ".mp3")
    audio.export(output_path, format="mp3")
    print(f"Processed audio saved to: {output_path}")
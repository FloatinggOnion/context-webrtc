import os
import wave
import io
import av
import json
import datetime
from collections import deque

from pydub import AudioSegment
import speech_recognition as sr
from transformers import pipeline
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")


class ContextRTTranslate:
    '''
    This class handles the real-time audio transcription and translation
    '''
    def __init__(self, upload_folder, api_key, buffer_size=5):
        self.UPLOAD_FOLDER = upload_folder
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        self.client = genai.client(api_key=api_key)
        self.transcription_buffer = deque(maxlen=buffer_size)  # Rolling transcript buffer
    
    def save_audio_chunks(self, media_data):
        '''
        Extracts the audio from the raw data sent from the frontend and saves it with a timestamp
        '''
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        audio_filename = os.path.join(self.UPLOAD_FOLDER, f"audio_{timestamp}.wav")

        # Extract audio
        input_buffer = io.BytesIO(media_data)
        output_buffer = io.BytesIO()
        container = av.open(input_buffer, format="webm")
        audio_stream = container.streams.audio[0]

        with av.open(output_buffer, "w", format="wav") as out_container:
            out_stream = out_container.add_stream("pcm_s16le", rate=48000)
            out_stream.layout = "mono"

            for frame in container.decode(audio_stream):
                packet = out_stream.encode(frame)
                if packet:
                    out_container.mux(packet)

        # Save extracted audio
        with open(audio_filename, "wb") as f:
            f.write(output_buffer.getvalue())

        return audio_filename

    def recognise_speech_from_stream(self, audio_stream):
        '''
        Performs speech recognition on the audio chunk
        '''
        recognizer = sr.Recognizer()
        audio_file = sr.AudioFile(audio_stream)
        with audio_file as source:
            audio = recognizer.record(source)
        try:
            text = sr.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return None
    
    def add_to_buffer(self, new_transcript):
        """
        Adds the new transcript to the rolling buffer.
        Ensures that the LLM receives enough context.
        """
        self.transcription_buffer.append(new_transcript)
        return " ".join(self.transcription_buffer)  # Return full context

    def contextualise_transcript(self, transcript):
        """
        Uses an LLM to improve the context and accuracy of the transcription.
        Processes the **last few transcripts** to improve sentence continuity.
        """
        full_context = self.add_to_buffer(transcript)  # Use full buffer

        prompt = f"""
        The following text is a raw speech transcript from a video. Improve the grammar, punctuation, and overall clarity while keeping the meaning intact. 
        Also ensure the conversation retains context.

        Original transcript:
        "{full_context}"

        Improved version:
        """
    
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                config=genai.types.GenerateContentConfig(
                    system_instruction='You are an expert in language modeling.',
                    max_output_tokens= 400,
                    top_k= 2,
                    top_p= 0.5,
                    temperature= 0.5,
                    response_mime_type= 'application/json',
                    stop_sequences= ['\n'],
                    seed=42,
                ),
                contents=prompt
            )
            return response.model_dump_json(exclude_none=True, indent=4)
        except Exception as e:
            print(f"⚠️ LLM Processing Error: {e}")
            return transcript  # Return original transcript if LLM fails
        
    def translate_text(self, text, target_lang="fr"):
        '''
        Translates the contextualised text using Helsinki Opus model
        '''
        model_name = 'Helsinki-NLP/opus-mt-tc-big-en-fr'
        pipe = pipeline('translation', model=model_name)
        return pipe(text)

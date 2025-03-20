import speech_recognition as sr

def recognise_speech_from_stream(audio_stream):
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
from fastapi import FastAPI, WebSocket
import json
from rt_translate import ContextRTTranslate

app = FastAPI()

UPLOAD_FOLDER = "uploads"
translator = ContextRTTranslate(upload_folder=UPLOAD_FOLDER, buffer_size=5)  # Initialize with buffer

connections = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections[client_id] = websocket
    print(f"🔴 Client {client_id} connected.")

    try:
        while True:
            data = await websocket.receive_text()
            message = eval(data)  

            if message["type"] == "video":
                media_data = await websocket.receive_bytes()
                audio_filename = translator.save_audio_chunks(media_data)

                print(f"✅ Saved audio: {audio_filename}")

                # Step 1: Transcribe audio
                transcript = translator.recognise_speech_from_stream(audio_filename)
                print(f"🎤 Transcribed text: {transcript}")

                if transcript:
                    # Step 2: Context modeling using buffer
                    refined_text = translator.contextualise_transcript(transcript)
                    print(f"📝 Contextualized transcript: {refined_text}")

                    # Step 3: Translation
                    translated_text = translator.translate_text(refined_text, target_lang="fr")
                    print(f"🌍 Translated transcript: {translated_text}")

                    # Send refined & translated transcript back to frontend
                    transcript_data = {
                        "type": "transcription",
                        "original": transcript,
                        "contextualized": refined_text,
                        "translated": translated_text,
                    }
                    await websocket.send_text(json.dumps(transcript_data))

                # Stream video back
                for client, conn in connections.items():
                    if client != client_id:
                        print(f"📹 Sending video to client {client}")
                        await conn.send_bytes(media_data)

    except Exception as e:
        print(f"⚠️ Error: {e}")

    finally:
        del connections[client_id]
        print(f"🔴 Client {client_id} disconnected.")

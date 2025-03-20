from fastapi import FastAPI, WebSocket
import datetime
import os
import io
import av
import json

from utils import recognise_speech_from_stream

app = FastAPI()

# Ensure uploads folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

connections = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections[client_id] = websocket
    print(f"🔴 Client {client_id} connected.")

    try:
        while True:
            data = await websocket.receive_text()
            message = eval(data)  # Convert string to dict

            if message["type"] == "offer":
                for client, conn in connections.items():
                    if client != client_id:
                        await conn.send_text(json.dumps(message))  # Send offer to receiver

            elif message["type"] == "answer":
                for client, conn in connections.items():
                    if client != client_id:
                        await conn.send_text(json.dumps(message))  # Send answer to caller

            elif message["type"] == "candidate":
                for client, conn in connections.items():
                    if client != client_id:
                        await conn.send_text(json.dumps(message))  # Send ICE candidate

            elif message["type"] == "video":
                media_data = await websocket.receive_bytes()
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                audio_filename = os.path.join(UPLOAD_FOLDER, f"audio_{timestamp}.wav")

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

                print(f"✅ Saved audio: {audio_filename}")

                # transcribe audio
                text = recognise_speech_from_stream(audio_filename)
                print(f"🎤 Transcribed text: {text}")

                # Stream video back
                for client, conn in connections.items():
                    if client != client_id:
                        print(f"📹 Sending video to client {client}")
                        print(media_data)
                        await conn.send_bytes(media_data)

    except Exception as e:
        print(f"⚠️ Error: {e}")

    finally:
        del connections[client_id]
        print(f"🔴 Client {client_id} disconnected.")

from fastapi import FastAPI, WebSocket
import asyncio
from pydub import AudioSegment
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack

app = FastAPI()
pcs = set()  # peer connections

class AudioSaver(MediaStreamTrack):
    kind = "audio"

    def __init__(self, track):
        super().__init__()
        self.track = track
        self.audio_data = bytearray()

    async def recv(self):
        frame = await self.track.recv()
        self.audio_data.extend(frame.to_bytes())

        # save every ~5 seconds (16kHz * 2 bytes/sample)
        if len(self.audio_data) >= 16000 * 2 * 5:
            self.save_audio()
            self.audio_data.clear()

        return frame

    def save_audio(self):
        audio_segment = AudioSegment(
            data=bytes(self.audio_data),
            sample_width=2,  # WebRTC 16-bit PCM
            frame_rate=16000,  # WebRTC common sample rate
            channels=1  # single channel / mono channel
        )
        audio_segment.export("output_audio.wav", format="wav")
        print("Saved audio chunk!")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    pc = RTCPeerConnection()
    pcs.add(pc)  # store the connection
    
    try:
        while True:
            data = await websocket.receive_json()
            if "sdp" in data:
                await pc.setRemoteDescription(RTCSessionDescription(**data))

                for t in pc.getTransceivers():
                    if t.kind == "audio":
                        pc.addTrack(AudioSaver(t.receiver.track))

                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                await websocket.send_json({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
    except Exception as e:
        print("WebSocket Error:", e)
    finally:
        pcs.discard(pc)  # clean up the peer connection when done
        await pc.close()
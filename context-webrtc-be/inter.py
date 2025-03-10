from fastapi import FastAPI
from fastapi.websockets import WebSocket, WebSocketDisconnect
from typing import List

from manager import MeetingManager, SignalManager


app = FastAPI()
clients: List[WebSocket] = []
meeting_manager = MeetingManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    # clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_bytes()   # receive_bytes() for binary data such as the audio or video
            await websocket.send_bytes(f"Message text was: {data}")
            await meeting_manager.rooms[client_id].broadcast(data, websocket)

    except Exception as e:
        print("WebSocket Error:", e)

    except WebSocketDisconnect:
        # clients.remove(websocket)
        meeting_manager.leave(client_id, websocket)
        print("Client disconnected")
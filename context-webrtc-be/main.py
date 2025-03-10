from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"New WebSocket connection: {client_id}")
    await websocket.accept()
    connected_clients[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from {client_id}: {data}")
            for client, conn in connected_clients.items():
                if client != client_id:
                    await conn.send_text(data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        del connected_clients[client_id]
        print(f"Connection {client_id} closed")
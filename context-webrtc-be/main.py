from fastapi import FastAPI, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the "uploads" directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# WebSocket endpoint for signaling
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        print("Received data:", data)

        # Handle signaling messages
        if data["type"] == "offer":
            await websocket.send_json({"type": "answer", "sdp": "..."})
        elif data["type"] == "ice-candidate":
            await websocket.send_json({"type": "ice-candidate", "candidate": "..."})

# Endpoint for uploading audio
@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    # Generate a unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"audio_{timestamp}.wav"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return JSONResponse(content={"message": "Audio uploaded successfully", "file_path": file_path})

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "ok"}
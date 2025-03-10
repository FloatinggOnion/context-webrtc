import React, { useRef, useEffect, useState } from "react";

const SERVER_URL = "ws://127.0.0.1:8000"; // WebSocket Server

const VideoCapture: React.FC = () => {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const peerConnection = useRef<RTCPeerConnection | null>(null);
  const [clientId] = useState(() => Math.random().toString(36).substring(2, 7));

  useEffect(() => {
    // Setup WebSocket connection
    ws.current = new WebSocket(`${SERVER_URL}/ws/${clientId}`);

    ws.current.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "offer") {
        console.log("Received offer:", message.data);
        if (!peerConnection.current) return;
        
        await peerConnection.current.setRemoteDescription(new RTCSessionDescription(message.data));
        const answer = await peerConnection.current.createAnswer();
        await peerConnection.current.setLocalDescription(answer);
        
        ws.current?.send(JSON.stringify({ type: "answer", data: answer }));
        console.log("Sent answer:", answer);
      } 
      
      else if (message.type === "answer") {
        console.log("Received answer:", message.data);
        if (!peerConnection.current) return;
        await peerConnection.current.setRemoteDescription(new RTCSessionDescription(message.data));
      } 
      
      else if (message.type === "candidate") {
        console.log("Received ICE candidate:", message.data);
        if (!peerConnection.current) return;
        await peerConnection.current.addIceCandidate(new RTCIceCandidate(message.data));
      }
    };

    // Get user media and initialize WebRTC connection
    navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then((stream) => {
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      peerConnection.current = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      stream.getTracks().forEach((track) => peerConnection.current?.addTrack(track, stream));

      peerConnection.current.ontrack = (event) => {
        console.log("🔥 Received remote track:", event.streams);
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = event.streams[0];
        }
      };
      

      peerConnection.current.onicecandidate = (event) => {
        if (event.candidate) {
          console.log("Sending ICE candidate:", event.candidate);
          ws.current?.send(JSON.stringify({ type: "candidate", data: event.candidate }));
        }
      };
    });

    return () => {
      ws.current?.close();
      peerConnection.current?.close();
    };
  }, []);

  const startCall = async () => {
    if (!peerConnection.current) return;
    console.log("Starting call...");

    const offer = await peerConnection.current.createOffer();
    await peerConnection.current.setLocalDescription(offer);

    ws.current?.send(JSON.stringify({ type: "offer", data: offer }));
    console.log("Sent offer:", offer);
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex gap-4">
        <div className="w-full flex flex-col gap-4">
          <h3 className="text-2xl font-semibold">Sender</h3>
          <video ref={localVideoRef} className="rounded-lg" autoPlay playsInline muted />
          <button className="rounded w-full py-2 bg-zinc-800 text-gray-200 hover:bg-zinc-700 transition-color duration 200" onClick={startCall}>
            Start Call
          </button>
        </div>
        <div className="w-full flex flex-col gap-4">
          <h3 className="text-2xl font-semibold">Receiver</h3>
          <video ref={remoteVideoRef} className="rounded-lg" autoPlay playsInline />
        </div>
      </div>
    </div>
  );
};

export default VideoCapture;

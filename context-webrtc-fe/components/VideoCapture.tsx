import React, { useRef, useEffect, useState } from "react";
import {
	sendSignalingData,
	connectWebSocket,
} from "../services/websocket.service";

type WebSocketMessageData =
	| { type: "offer"; sdp: string }
	| { type: "answer"; sdp: string }
	| { type: "ice-candidate"; candidate: string };

const VideoCapture: React.FC = () => {
	const videoRef = useRef<HTMLVideoElement>(null);
	const remoteVideoRef = useRef<HTMLVideoElement>(null);
	const [peerConnection, setPeerConnection] =
		useState<RTCPeerConnection | null>(null);
	const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
		null
	);
	const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

	useEffect(() => {
		const startCapture = async () => {
			try {
				const stream = await navigator.mediaDevices.getUserMedia({
					video: true,
					audio: true,
				});
				if (videoRef.current) {
					videoRef.current.srcObject = stream;
				}
			} catch (error) {
				console.error("Error accessing media devices:", error);
			}
		};

		startCapture();

		// Connect to WebSocket
		connectWebSocket(handleWebSocketMessage);

		// Cleanup
		return () => {
			if (peerConnection) {
				peerConnection.close();
			}
			if (mediaRecorder) {
				mediaRecorder.stop();
			}
		};
	}, []);

	const handleWebSocketMessage = async (data: WebSocketMessageData) => {
		if (data.type === "offer") {
			await handleOffer(data);
		} else if (data.type === "answer") {
			await handleAnswer(data);
		} else if (data.type === "ice-candidate") {
			await handleICECandidate(data);
		}
	};

	const createPeerConnection = async () => {
		const configuration = {
			iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
		};
		const pc = new RTCPeerConnection(configuration);
		setPeerConnection(pc);

		// Add local stream to peer connection
		const localStream = videoRef.current?.srcObject as MediaStream;
		if (localStream) {
			localStream
				.getTracks()
				.forEach((track) => pc.addTrack(track, localStream));
		}

		// Handle ICE candidates
		pc.onicecandidate = (event) => {
			if (event.candidate) {
				sendSignalingData({
					type: "ice-candidate",
					candidate: event.candidate,
				});
			}
		};

		// Handle remote stream
		pc.ontrack = (event) => {
			if (remoteVideoRef.current) {
				remoteVideoRef.current.srcObject = event.streams[0];
			}

			// Start recording the remote audio
			const remoteStream = event.streams[0];
			const audioTracks = remoteStream.getAudioTracks();
			if (audioTracks.length > 0) {
				startRecording(remoteStream);
			}
		};

		// Create and send SDP offer
		const offer = await pc.createOffer();
		await pc.setLocalDescription(offer);
		sendSignalingData({ type: "offer", sdp: offer.sdp });
	};

	const handleOffer = async (data: { sdp: string }) => {
		if (!peerConnection) return;
		await peerConnection.setRemoteDescription(
			new RTCSessionDescription({ type: "offer", sdp: data.sdp })
		);
		const answer = await peerConnection.createAnswer();
		await peerConnection.setLocalDescription(answer);
		sendSignalingData({ type: "answer", sdp: answer.sdp });
	};

	const handleAnswer = async (data: { sdp: string }) => {
		if (!peerConnection) return;
		await peerConnection.setRemoteDescription(
			new RTCSessionDescription({ type: "answer", sdp: data.sdp })
		);
	};

	const handleICECandidate = async (data: { candidate: string }) => {
		if (!peerConnection) return;
		await peerConnection.addIceCandidate(JSON.parse(data.candidate));
	};

	const startRecording = (stream: MediaStream) => {
		const recorder = new MediaRecorder(stream);
		setMediaRecorder(recorder);

		recorder.ondataavailable = (event) => {
			setAudioChunks((chunks) => [...chunks, event.data]);
		};

		recorder.onstop = () => {
			const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
			uploadAudio(audioBlob);
		};

		recorder.start();
	};

	const stopRecording = () => {
		if (mediaRecorder) {
			console.log("Stopping media recorder");
			mediaRecorder.stop();
		}
	};

	const uploadAudio = async (audioBlob: Blob) => {
		const formData = new FormData();
		formData.append("file", audioBlob, "recorded_audio.wav");

		try {
			const response = await fetch("http://localhost:8000/upload-audio", {
				method: "POST",
				body: formData,
			});
			console.log("Audio upload response:", await response.json());
		} catch (error) {
			console.error("Error uploading audio:", error);
		}
	};

	return (
		<div className="flex flex-col gap-6">
			<div className="flex gap-4">
				<div className="w-full">
					<h3 className="text-2xl font-semibold">Sender</h3>
					<video
						ref={videoRef}
						className="rounded-lg"
						autoPlay
						playsInline
						muted
					/>
				</div>
				<div className="w-full">
					<h3 className="text-2xl font-semibold">Receiver</h3>
					<video ref={remoteVideoRef} autoPlay playsInline />
				</div>
			</div>
			<div className="flex gap-2">
				<button
					onClick={createPeerConnection}
					className="w-full h-full py-2 text-lg rounded-lg bg-zinc-800 text-gray-200 hover:bg-zinc-700"
				>
					Connect
				</button>
				<button
					onClick={stopRecording}
					className="w-full h-full py-2 text-lg rounded-lg bg-zinc-800 text-gray-200 hover:bg-zinc-700"
				>
					Stop Recording
				</button>
			</div>
		</div>
	);
};

export default VideoCapture;

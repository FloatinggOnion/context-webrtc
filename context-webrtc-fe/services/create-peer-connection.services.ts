import sendSignalingData from "./send-signaling-data.services";

const createPeerConnection = async () => {
	const configuration = {
		iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
	};
	const peerConnection = new RTCPeerConnection(configuration);

	// Add the local stream to the peer connection
	const localStream = videoRef.current.srcObject;
	localStream
		.getTracks()
		.forEach((track) => peerConnection.addTrack(track, localStream));

	// Handle ICE candidates
	peerConnection.onicecandidate = (event) => {
		if (event.candidate) {
			// Send the ICE candidate to the backend
			sendSignalingData({
				type: "ice-candidate",
				candidate: event.candidate,
			});
		}
	};

	// Handle remote stream
	peerConnection.ontrack = (event) => {
		const remoteVideo = document.getElementById("remote-video");
		if (remoteVideo) {
			remoteVideo.srcObject = event.streams[0];
		}
	};

	return peerConnection;
};


export default createPeerConnection;
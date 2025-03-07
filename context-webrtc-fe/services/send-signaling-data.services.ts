const sendSignalingData = async (data) => {
	await fetch("https://localhost:8000/ws", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data),
	});
};


export default sendSignalingData;
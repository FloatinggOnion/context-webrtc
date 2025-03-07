// import { useState, useRef, useEffect } from "react";
import VideoCapture from "../components/VideoCapture";

function App() {
	return (
		<div className="h-screen w-full flex flex-col items-center justify-center gap-6">
			<h2 className="font-semibold text-5xl border-2 border-dashed px-8 py-2 rounded-lg shadow-lg">
				Context WebRTC
			</h2>
			<div className="mx-auto rounded-lg">
				<VideoCapture />
			</div>
		</div>
	);
}

export default App;

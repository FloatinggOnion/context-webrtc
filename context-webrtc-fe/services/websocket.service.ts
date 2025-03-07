let socket: WebSocket;

// @ts-expect-error
export const connectWebSocket = (onMessage: (data: any) => void) => {
    socket = new WebSocket("ws://localhost:8000/ws");

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
    };
};

// @ts-expect-error
export const sendSignalingData = (data: any) => {
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(data));
  }
};
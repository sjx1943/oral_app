const { WebSocketServer } = require('ws');

const wss = new WebSocketServer({ port: 8080 });

console.log('WebSocket server is running on port 8080');

wss.on('connection', function connection(ws) {
  console.log('A new client connected!');

  ws.on('error', console.error);

  ws.on('message', function message(data) {
    console.log('received: %s', data);
    // Echo the message back to the client
    ws.send(`Echo: ${data}`);
  });

  ws.send('Welcome to the WebSocket server!');
});

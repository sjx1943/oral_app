const { WebSocketServer, WebSocket } = require('ws');
const jwt = require('jsonwebtoken');
const url = require('url');

const wss = new WebSocketServer({ port: 8080 });

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) {
  console.error("FATAL ERROR: JWT_SECRET is not defined in the environment variables.");
  console.error("Available environment variables:", Object.keys(process.env).filter(key => key.includes('JWT')));
  process.exit(1);
}

const AI_SERVICE_URL = 'ws://ai-omni-service:8082/stream';

console.log('WebSocket server is running on port 8080');

wss.on('connection', async function connection(clientWs, req) {
  console.log('A new client is attempting to connect...');

  try {
    const queryObject = url.parse(req.url, true).query;
    const token = queryObject.token;

    if (!token) {
      console.log('Connection rejected: No token provided.');
      clientWs.close(1008, 'Authorization token is required.');
      return;
    }

    let decoded;
    try {
      decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
      console.log(`Connection rejected: Invalid token. ${err.message}`);
      clientWs.close(1008, 'Invalid or expired authorization token.');
      return;
    }

    const userId = decoded.id;
    const sessionId = queryObject.sessionId;

    if (!sessionId) {
      console.log('Connection rejected: No sessionId provided.');
      clientWs.close(1008, 'Session ID is required.');
      return;
    }

    console.log(`Token verified for user ID: ${userId}, Session ID: ${sessionId}`);
    clientWs.userId = userId;
    clientWs.sessionId = sessionId;

    const aiServiceWs = new WebSocket(AI_SERVICE_URL);

    aiServiceWs.on('open', () => {
      console.log(`Successfully connected to AI Service for user ${userId} and session ${sessionId}`);
      clientWs.send(JSON.stringify({ type: 'info', message: 'Welcome! Your connection is authenticated and bridged to the AI service.' }));

      // NOW that the AI service connection is open, start forwarding messages.
      clientWs.on('message', (message) => {
        // The 'ws' library receives binary data from the browser as a Buffer.
        // We need to wrap this in the JSON format expected by ai-omni-service.
        if (aiServiceWs.readyState === WebSocket.OPEN) {
          if (Buffer.isBuffer(message)) {
            console.log(`Wrapping binary message of size ${message.length} from user ${userId}, session ${sessionId} into JSON for AI service.`);
            const messageForAI = JSON.stringify({
              type: 'audio_stream',
              userId: userId,
              sessionId: sessionId, // Include sessionId here
              audioBuffer: message.toString('base64'), // Encode buffer as base64 string
              context: {} // Add empty context for now
            });
            aiServiceWs.send(messageForAI);
          } else {
             // If it's not a buffer, we could assume it's a text message from client
             // For now, the client only sends audio, so we'll log this.
             console.log(`Received non-binary message from user ${userId}. Ignoring.`);
          }
        }
      });

      // Also, set up the return path.
      aiServiceWs.on('message', (message) => {
        // The message from the AI service is always a Buffer, whether it's TTS audio or a JSON string.
        // We need to differentiate. A simple way is to try parsing it as JSON.
        if (clientWs.readyState === WebSocket.OPEN) {
          let isJson = false;
          let messageString = '';
          try {
            // We have to convert buffer to string to parse.
            messageString = message.toString('utf8');
            JSON.parse(messageString);
            isJson = true;
          } catch (e) {
            // This is not a JSON string, so it must be binary audio data.
            isJson = false;
          }

          if (isJson) {
            console.log(`Forwarding text message from AI service to user ${userId}: ${messageString}`);
            clientWs.send(messageString); // Send as text
          } else {
            // This is binary audio data. Forward it directly.
            console.log(`Forwarding binary message of size ${message.length} from AI service to user ${userId}.`);
            clientWs.send(message, { binary: true }); // Send as binary
          }
        }
      });
    });

    // --- Keep the lifecycle event handlers outside ---

    clientWs.on('close', () => {
      console.log(`Client connection closed for user ${userId}. Closing connection to AI service.`);
      if (aiServiceWs.readyState === WebSocket.OPEN || aiServiceWs.readyState === WebSocket.CONNECTING) {
        aiServiceWs.close();
      }
    });

    aiServiceWs.on('close', () => {
      console.log(`Connection to AI service closed for user ${userId}.`);
      if (clientWs.readyState === WebSocket.OPEN || clientWs.readyState === WebSocket.CONNECTING) {
        clientWs.close(1011, 'AI service connection lost.');
      }
    });

    clientWs.on('error', (error) => {
      console.error(`Error on client connection for user ${userId}:`, error);
      aiServiceWs.close();
    });

    aiServiceWs.on('error', (error) => {
      console.error(`Error on AI service connection for user ${userId}:`, error);
      clientWs.close(1011, 'Internal AI service connection error.');
    });

  } catch (error) {
    console.error('An unexpected error occurred during connection setup:', error);
    clientWs.close(1011, 'Internal server error');
  }
});
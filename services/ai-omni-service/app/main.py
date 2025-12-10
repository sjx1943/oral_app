import os
import json
import asyncio
import threading
import logging
import base64
from contextlib import asynccontextmanager
from http.server import HTTPServer, BaseHTTPRequestHandler

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

import dashscope
import websocket
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality
try:
    from app.prompt_manager import prompt_manager
except ImportError:
    try:
        from prompt_manager import prompt_manager
    except ImportError:
        # Fallback if both fail, though one should work
        pass

# Load env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure DashScope API Key
dashscope.api_key = os.getenv("QWEN3_OMNI_API_KEY")

# --- Health Check Server (Port 8081) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "OK", "service": "ai-omni-service-python", "aiService": {"usingRealAPI": True}}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    port = int(os.getenv("HEALTH_CHECK_PORT", 8081))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    logger.info("STARTING NEW VERSION WITH RECONNECT LOGIC (VERIFIED)")
    server.serve_forever()

# --- Main FastAPI App (Port 8082) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run health server in background
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    yield
    # Shutdown logic if needed

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DashScope Integration ---

class WebSocketCallback(OmniRealtimeCallback):
    def __init__(self, websocket: WebSocket, loop: asyncio.AbstractEventLoop, user_context: dict = None):
        self.websocket = websocket
        self.loop = loop
        self.user_context = user_context or {}
        self.conversation = None # Will be attached later

    def on_open(self) -> None:
        logger.info("DashScope Connection Open")
        # Notify client
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_json({
                "type": "connection_established", 
                "payload": {
                    "connectionId": "python-session",
                    "message": "Connected to Qwen3-Omni (Python)",
                    "usingRealAPI": True
                }
            }), 
            self.loop
        )
        
        # Inject System Prompt
        if self.conversation:
             system_prompt = prompt_manager.generate_system_prompt(self.user_context)
             logger.info(f"Sending System Prompt: {system_prompt[:100]}...")
             # Use update_session to set system instructions
             self.conversation.update_session(
                 output_modalities=[MultiModality.TEXT, MultiModality.AUDIO],
                 instructions=system_prompt,
                 voice="Cherry"
             )

    def on_event(self, response: dict) -> None:
        # Debug: Print first 500 chars of event to identify structure
        logger.info(f"DEBUG EVENT: {json.dumps(response)[:500]}")
        
        # 1. Determine Event Name
        event_name = response.get('type') # 直接使用顶层 type 字段
        payload = response # 整个 response 就是 payload，因为数据在 delta 里
        
        async def send_to_client():
            try:
                # Handle Audio Output
                if event_name == 'response.audio.delta': 
                     audio_data = payload.get('delta') 
                     if audio_data:
                         await self.websocket.send_json({
                             "type": "audio_response",
                             "payload": audio_data 
                         })
                         
                # Handle Text Output (LLM Response)
                elif event_name == 'response.audio_transcript.delta': 
                     text = payload.get('delta') 
                     if text:
                        await self.websocket.send_json({
                            "type": "text_response",
                            "payload": text
                        })
                        
                # Handle ASR (Input Transcription) - Now this is the LLM output too
                # No separate handling needed, it's covered by 'response.audio_transcript.delta'
            except Exception as e:
                logger.error(f"Error sending to client: {e}")

        asyncio.run_coroutine_threadsafe(send_to_client(), self.loop)

    def on_close(self, close_status_code: int, close_msg: str) -> None:
        logger.info(f"DashScope Connection Closed: {close_msg}")

# --- Routes ---

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    
    # Mock User Context (In production, this would come from the connection params or DB)
    user_context = {
        "targetLanguage": "English",
        "nativeLanguage": "Chinese",
        "proficiencyLevel": "Intermediate",
        "learningGoals": "Improving pronunciation and business vocabulary",
        "interests": ["Technology", "Travel", "Movies"],
        "historySummary": ""
    }
    
    conversation = None
    callback = None

    def connect_dashscope():
        nonlocal conversation, callback
        callback = WebSocketCallback(websocket, loop, user_context)
        conversation = OmniRealtimeConversation(
            model=os.getenv("QWEN3_OMNI_MODEL", "qwen3-omni-flash-realtime"),
            callback=callback,
            # Use endpoint if provided, else default
            # url=os.getenv("QWEN3_OMNI_BASE_URL", "wss://dashscope.aliyuncs.com/api-ws/v1/realtime") 
        )
        callback.conversation = conversation
        conversation.connect()
        return conversation

    try:
        conversation = connect_dashscope()
    except Exception as e:
        logger.error(f"Initial DashScope connection failed: {e}")
        # Optionally notify client about error
        await websocket.close(code=1011, reason="Upstream connection failed")
        return
    
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            msg_type = data.get('type')
            payload = data.get('payload', {})
            
            try:
                if msg_type == 'audio_stream':
                    # payload has 'audioBuffer' (base64)
                    audio_b64 = payload.get('audioBuffer')
                    if audio_b64:
                        conversation.append_audio(audio_b64)
                
                elif msg_type == 'text_message':
                    text = payload.get('text')
                    if text:
                        logger.info(f"DEBUG: Processing user text: {text}")
                        # Pass user input directly as instructions to ensure response
                        instructions = f"User said: {text}"
                        conversation.create_response(instructions=instructions)
                        logger.info(f"DEBUG: Sent response.create with instructions: {instructions}")
                        
                elif msg_type == 'ping':
                    await websocket.send_json({"type": "pong"})
            
            except (websocket.WebSocketConnectionClosedException, BrokenPipeError) as e:
                logger.warning(f"DashScope connection lost ({e}), reconnecting...")
                try:
                    try:
                        conversation.close()
                    except:
                        pass
                    
                    conversation = connect_dashscope()
                    
                    # Retry sending
                    if msg_type == 'text_message':
                         conversation.send_raw(json.dumps(msg))
                         conversation.create_response()
                    elif msg_type == 'audio_stream':
                         conversation.append_audio(audio_b64)
                         
                    logger.info("Reconnected and retried message.")
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect: {reconnect_error}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        try:
            if conversation: conversation.close()
        except:
            pass

# --- Compatible HTTP Endpoints ---

class TextRequest(BaseModel):
    text: str
    userId: str = None
    context: dict = None

class ChatRequest(BaseModel):
    messages: list
    userId: str = None

@app.post("/api/process/text")
async def process_text(req: TextRequest):
    return {"code": 200, "message": "Please use WebSocket /stream for interaction", "data": {"response": "Text processed (Mock)"}}

@app.post("/api/process/audio")
async def process_audio(request: Request):
    return {"code": 200, "message": "Please use WebSocket /stream for interaction", "data": {"response": "Audio processed (Mock)"}}

@app.post("/api/ai/chat")
async def chat(req: ChatRequest):
    # Mock response for compatibility
    return {
        "code": 200, 
        "message": "Chat processed successfully",
        "data": {
            "messages": req.messages + [{"role": "assistant", "content": [{"text": "I am migrated to Python! Please connect via WebSocket."}]}],
            "response": "I am migrated to Python! Please connect via WebSocket.",
            "timestamp": "2025-12-10T00:00:00Z"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("AI_SERVICE_PORT", 8082))
    uvicorn.run(app, host="0.0.0.0", port=port)
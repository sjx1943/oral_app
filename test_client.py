import asyncio
import websockets
import json
import base64
import sys

async def receive_loop(websocket):
    """Handles receiving messages from the server."""
    with open("output.pcm", "wb") as f:
        try:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                msg_type = data.get('type')
                payload = data.get('payload')
                
                if msg_type == 'text_response':
                    # Print text chunk immediately
                    sys.stdout.write(payload)
                    sys.stdout.flush()
                elif msg_type == 'audio_response':
                    # Decode and save audio
                    if payload:
                        audio_data = base64.b64decode(payload)
                        f.write(audio_data)
                elif msg_type == 'connection_established':
                    print(f"\n[System] Session Established: {payload.get('message')}")
                elif msg_type == 'error':
                    print(f"\n[Error from Server]: {payload}")
        except websockets.exceptions.ConnectionClosed:
            print("\n[System] Connection closed by server.")
        except Exception as e:
            print(f"\n[Error] Receive loop error: {e}")

async def send_loop(websocket):
    """Handles reading user input and sending it to the server."""
    # Send initial greeting automatically
    initial_text = "Hello, please introduce yourself."
    initial_msg = {
        "type": "text_message", 
        "payload": {"text": initial_text}
    }
    await websocket.send(json.dumps(initial_msg))
    print(f"[You]: {initial_text}")
    print("-" * 50)
    print("Receiving response... (Type below to reply, 'quit' to exit)")
    
    loop = asyncio.get_running_loop()
    while True:
        # Run input() in a separate thread to avoid blocking the async event loop
        # sys.stdout.write("\n[You]: ")
        # sys.stdout.flush()
        user_input = await loop.run_in_executor(None, sys.stdin.readline)
        user_input = user_input.strip()
        
        if not user_input:
            continue
            
        if user_input.lower() in ['quit', 'exit']:
            print("Exiting...")
            break
            
        msg = {
            "type": "text_message",
            "payload": {"text": user_input}
        }
        try:
            await websocket.send(json.dumps(msg))
        except Exception as e:
            print(f"\n[Error] Failed to send: {e}")
            break

async def test():
    uri = "ws://localhost:8080/api/ai/ws/stream"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Run receive and send loops concurrently
            receive_task = asyncio.create_task(receive_loop(websocket))
            send_task = asyncio.create_task(send_loop(websocket))
            
            # Wait for user to quit or connection to close
            done, pending = await asyncio.wait(
                [receive_task, send_task], 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                
    except Exception as e:
        print(f"\n[Error] Connection failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
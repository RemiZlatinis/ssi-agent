"""
WebSocket server to receive and handle log messages from the watcher.
"""

import asyncio
import websockets

# Store connected clients
CLIENTS = set()


async def register(websocket):
    """Register a new client connection"""
    CLIENTS.add(websocket)
    print("Client connected")


async def unregister(websocket):
    """Unregister a client connection"""
    CLIENTS.remove(websocket)
    print("Client disconnected")


async def broadcast(message):
    """Broadcast message to all connected clients"""
    if CLIENTS:
        await asyncio.gather(*[client.send(message) for client in CLIENTS])


async def handle_connection(websocket):
    """Handle incoming WebSocket connections"""
    await register(websocket)
    try:
        async for message in websocket:
            print(f"Received log: {message}")
            # Broadcast the message to all connected clients
            # await broadcast(message)
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        await unregister(websocket)


async def main():
    while True:
        try:
            async with websockets.serve(
                handle_connection,
                "localhost",
                5000,
                ping_interval=20,
                ping_timeout=60,
            ):
                print("WebSocket server started on ws://localhost:5000")
                await asyncio.Future()  # run forever
        except Exception as e:
            print(f"Server error: {e}. Restarting in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())

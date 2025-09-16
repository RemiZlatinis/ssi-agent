"""
WebSocket server to receive and handle event-driven messages from the watcher.
"""

import asyncio
import json
from typing import Any

import websockets

from .models import (
    AgentHelloEvent,
    ServiceAddedEvent,
    ServiceRemovedEvent,
    StatusUpdateEvent,
)

# Store connected clients and their state
CLIENTS: dict[str, websockets.WebSocketServerProtocol] = {}
AGENTS_STATE: dict[str, dict[str, Any]] = {}
# Track which WebSocket belongs to which agent
WEBSOCKET_TO_AGENT: dict[websockets.WebSocketServerProtocol, str] = {}


async def register_agent(
    websocket: websockets.WebSocketServerProtocol, agent_key: str
) -> None:
    """Register a new agent connection"""
    CLIENTS[agent_key] = websocket
    AGENTS_STATE[agent_key] = {"services": {}}
    print(f"Agent {agent_key} connected")


async def unregister_agent(agent_key: str) -> None:
    """Unregister an agent connection and clean up state"""
    if agent_key in CLIENTS:
        del CLIENTS[agent_key]
    if agent_key in AGENTS_STATE:
        del AGENTS_STATE[agent_key]
    print(f"Agent {agent_key} disconnected")


async def handle_agent_hello(
    websocket: websockets.WebSocketServerProtocol, data: dict[str, Any]
) -> None:
    """Handle agent_hello event"""
    try:
        event = AgentHelloEvent(**data)
        await register_agent(websocket, event.agent_key)
        WEBSOCKET_TO_AGENT[websocket] = event.agent_key

        # Store agent services
        for service in event.services:
            AGENTS_STATE[event.agent_key]["services"][service.id] = service.model_dump()

        print(f"Agent {event.agent_key} registered with {len(event.services)} services")
    except Exception as e:
        print(f"Error handling agent_hello: {e}")


async def handle_service_added(
    websocket: websockets.WebSocketServerProtocol, data: dict[str, Any]
) -> None:
    """Handle service_added event"""
    try:
        agent_key = WEBSOCKET_TO_AGENT.get(websocket)
        if not agent_key:
            print("Unknown WebSocket connection for service_added event")
            return

        event = ServiceAddedEvent(**data)
        if agent_key in AGENTS_STATE:
            AGENTS_STATE[agent_key]["services"]
            [event.service.id] = event.service.model_dump()
            print(f"Service {event.service.id} added to agent {agent_key}")
        else:
            print(f"Unknown agent {agent_key} for service_added event")
    except Exception as e:
        print(f"Error handling service_added: {e}")


async def handle_service_removed(
    websocket: websockets.WebSocketServerProtocol, data: dict[str, Any]
) -> None:
    """Handle service_removed event"""
    try:
        agent_key = WEBSOCKET_TO_AGENT.get(websocket)
        if not agent_key:
            print("Unknown WebSocket connection for service_removed event")
            return

        event = ServiceRemovedEvent(**data)
        if agent_key in AGENTS_STATE:
            if event.service_id in AGENTS_STATE[agent_key]["services"]:
                del AGENTS_STATE[agent_key]["services"][event.service_id]
                print(f"Service {event.service_id} removed from agent {agent_key}")
            else:
                print(f"Service {event.service_id} not found for agent {agent_key}")
        else:
            print(f"Unknown agent {agent_key} for service_removed event")
    except Exception as e:
        print(f"Error handling service_removed: {e}")


async def handle_status_update(
    websocket: websockets.WebSocketServerProtocol, data: dict[str, Any]
) -> None:
    """Handle status_update event"""
    try:
        agent_key = WEBSOCKET_TO_AGENT.get(websocket)
        if not agent_key:
            print("Unknown WebSocket connection for status_update event")
            return

        event = StatusUpdateEvent(**data)
        print(
            f"Status update from agent {agent_key}:"
            f" {event.update.service_id} - {event.update.status}"
        )

        # Here you could broadcast to connected clients, store in database, etc.
        # For now, just log it

    except Exception as e:
        print(f"Error handling status_update: {e}")


async def handle_connection(websocket: websockets.WebSocketServerProtocol) -> None:
    """Handle incoming WebSocket connections"""
    agent_key = None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                event_type = data.get("event")

                if event_type == "agent_hello":
                    await handle_agent_hello(websocket, data)
                    agent_key = data.get("agent_key")
                elif event_type == "service_added":
                    await handle_service_added(websocket, data)
                elif event_type == "service_removed":
                    await handle_service_removed(websocket, data)
                elif event_type == "status_update":
                    await handle_status_update(websocket, data)
                else:
                    print(f"Received unknown event type: {event_type}")

            except json.JSONDecodeError as e:
                print(f"Invalid JSON received: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Error handling connection: {e}")
    finally:
        if agent_key:
            await unregister_agent(agent_key)


async def main() -> None:
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

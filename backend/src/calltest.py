# agent.py
import os
import json
import base64
import asyncio
import argparse
import re
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import openai

# Load environment variables from .env
load_dotenv()

# Required configuration (set these in your .env file)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PHONE_NUMBER_FROM = os.getenv("PHONE_NUMBER_FROM")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
raw_domain = os.getenv("DOMAIN", "")
# Strip protocol (https://) and trailing slashes from DOMAIN (e.g. your ngrok URL)
DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain)
PORT = int(os.getenv("PORT", 6060))
# Optionally, set the discussion topic (default is "technology")
TOPIC = os.getenv("TOPIC", "technology")

# This is the system message for the AI session.
SYSTEM_MESSAGE = (
    f"You are a friendly and engaging AI voice assistant. "
    f"Your task is to call a user, ask them about {TOPIC}, engage in conversation, "
    "and then, when the call is over, summarize the discussion in a short paragraph. "
    "Make sure your questions are clear and polite."
)

VOICE = "alloy"  # Change as needed (controls the AI voice)
LOG_EVENT_TYPES = [
    "error", "response.content.done", "rate_limits.updated", "response.done",
    "input_audio_buffer.committed", "input_audio_buffer.speech_stopped",
    "input_audio_buffer.speech_started", "session.created"
]

# Initialize FastAPI and Twilio client
app = FastAPI()
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Set OpenAI API key for completions
openai.api_key = OPENAI_API_KEY

# Global list to collect text (if available) from the call for summarization
conversation_transcript = []

@app.get("/", response_class=JSONResponse)
async def index():
    return {"message": "AI Voice Assistant is running."}

@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    print("A client (Twilio) connected to our media stream endpoint.")
    await websocket.accept()

    # Connect to OpenAI’s Realtime API via WebSocket
    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
        headers={
            "Authorization": f"Bearer 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",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data["event"] == "media" and openai_ws.open:
                        # Forward incoming audio (encoded in base64) to OpenAI
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"]
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data["event"] == "start":
                        stream_sid = data["start"]["streamSid"]
                        print(f"Media stream started with SID: {stream_sid}")
            except WebSocketDisconnect:
                print("Twilio WebSocket disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response["type"] in LOG_EVENT_TYPES:
                        print(f"OpenAI event: {response['type']}")
                    # If a text delta is received, add it to our transcript
                    if response["type"] == "response.text_delta" and response.get("delta"):
                        conversation_transcript.append(response["delta"])
                    # If audio data is available, proxy it back to Twilio
                    if response["type"] == "response.audio.delta" and response.get("delta"):
                        try:
                            audio_payload = base64.b64encode(
                                base64.b64decode(response["delta"])
                            ).decode("utf-8")
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": audio_payload},
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio delta: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def initialize_session(openai_ws):
    """Set up the initial session with OpenAI and have the AI ask about the topic."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print("Initializing OpenAI session...")
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first by sending an initial conversation item.
    initial_message = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Hello! I’d love to hear your thoughts on {TOPIC}. What do you think about it?"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_message))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def check_number_allowed(to):
    """Verify that the given phone number is allowed (e.g. is one of your verified numbers)."""
    try:
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=to)
        if incoming_numbers:
            return True

        outgoing_caller_ids = client.outgoing_caller_ids.list(phone_number=to)
        if outgoing_caller_ids:
            return True

        return False
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return False

async def make_call(phone_number_to_call: str):
    """Initiate an outbound call via Twilio and connect it to our media stream endpoint."""
    if not phone_number_to_call:
        raise ValueError("Please provide a phone number to call.")

    allowed = await check_number_allowed(phone_number_to_call)
    if not allowed:
        raise ValueError(f"The number {phone_number_to_call} is not allowed for outbound calls.")

    # Create TwiML that instructs Twilio to open a WebSocket connection
    twiml_response = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response>"
        f"<Connect>"
        f'<Stream url="wss://{DOMAIN}/media-stream" />'
        f"</Connect>"
        f"</Response>"
    )
    call = client.calls.create(
        from_=PHONE_NUMBER_FROM,
        to=phone_number_to_call,
        twiml=twiml_response
    )
    print(f"Call initiated with SID: {call.sid}")
    return call.sid

async def conclude_call_and_summarize():
    """Use OpenAI’s ChatCompletion endpoint to generate a summary of the conversation."""
    transcript_text = " ".join(conversation_transcript)
    prompt = (
        "Summarize the following conversation in a concise paragraph:\n\n"
        f"{transcript_text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a summarization assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        summary = response.choices[0].message["content"].strip()
    except Exception as e:
        summary = f"Failed to generate summary: {e}"
    print("\n=== Conversation Summary ===")
    print(summary)
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Phone Call Agent")
    parser.add_argument(
        "--call",
        required=True,
        help="Phone number to call (in E.164 format, e.g. +1234567890)",
    )
    args = parser.parse_args()
    phone_number = args.call

    # Start the outbound call
    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_call(phone_number))

    # Run the FastAPI server in a background thread to handle Twilio WebSocket events.
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=PORT)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("\nCall is in progress. When you wish to end the call and generate a summary, press Enter.")
    input("Press Enter to conclude the call...")

    print("Concluding the call and generating summary...")
    loop.run_until_complete(conclude_call_and_summarize())

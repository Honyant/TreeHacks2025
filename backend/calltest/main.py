import os
import json
import base64
import asyncio
import argparse
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import re
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
PHONE_NUMBER_FROM = os.getenv("PHONE_NUMBER_FROM")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
raw_domain = os.getenv("DOMAIN", "")
DOMAIN = re.sub(
    r"(^\w+:|^)\/\/|\/+$", "", raw_domain
)  # Strip protocols and trailing slashes from DOMAIN

print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
print(f"TWILIO_AUTH_TOKEN: {TWILIO_AUTH_TOKEN}")
print(f"PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"DOMAIN: {DOMAIN}")
PORT = int(os.getenv("PORT", 6060))
SYSTEM_MESSAGE = (
    "You are an AI voice assistant to ask the user questions and gather information."
)
TOPIC = "Your day"
VOICE = "alloy"
LOG_EVENT_TYPES = [
    "error",
    "response.content.done",
    "rate_limits.updated",
    "response.done",
    "input_audio_buffer.committed",
    "input_audio_buffer.speech_stopped",
    "input_audio_buffer.speech_started",
    "session.created",
]

app = FastAPI()

if not (
    TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM and OPENAI_API_KEY
):
    raise ValueError(
        "Missing Twilio and/or OpenAI environment variables. Please set them in the .env file."
    )

# Initialize Twilio client
client = Client(
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Add this new class for the request body
class CallRequest(BaseModel):
    phone_number: str
    topic: str
    max_duration: Optional[int] = 300  # default 5 minutes


# Add a dictionary to store call summaries
call_summaries = {}


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    conversation_transcript = []

    async with websockets.connect(
        "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        },
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data["event"] == "media":
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data["media"]["payload"],
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data["event"] == "start":
                        stream_sid = data["start"]["streamSid"]
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                # if openai_ws.open:
                #     await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, conversation_transcript
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response["type"] in LOG_EVENT_TYPES:
                        # print(f"Received event: {response['type']}", response)
                        pass
                    if response["type"] == "session.updated":
                        # print("Session updated successfully:", response)
                        pass
                    if response["type"] == "response.audio.delta" and response.get(
                        "delta"
                    ):
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
                            print(f"Error processing audio data: {e}")
                    if response["type"] == "response.content.delta":
                        if "delta" in response and "text" in response["delta"]:
                            conversation_transcript.append(response["delta"]["text"])
                        print(f"Total transcript: {conversation_transcript}")
                    # Handle end of call
                    if response["type"] == "session.done":
                        summary = await generate_summary(conversation_transcript)
                        print(f"Summary: {summary}")
                        if stream_sid:
                            call_summaries[stream_sid] = summary
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    global TOPIC
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        f"Greet the user with 'Hello there! As you are the expert on {TOPIC}, I'm here to ask you a few questions about {TOPIC}, for the purpose of our investigation for our research at Stanford."
                    ),
                }
            ],
        },
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
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
        },
    }
    print("Sending session update:", json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)


async def check_number_allowed(to):
    """Check if a number is allowed to be called."""
    try:
        # Uncomment these lines to test numbers. Only add numbers you have permission to call
        # OVERRIDE_NUMBERS = ['+18005551212']
        # if to in OVERRIDE_NUMBERS:
        # return True

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
    """Make an outbound call."""
    if not phone_number_to_call:
        raise ValueError("Please provide a phone number to call.")

    # is_allowed = await check_number_allowed(phone_number_to_call)
    # if not is_allowed:
    #     raise ValueError(f"The number {phone_number_to_call} is not recognized as a valid outgoing number or caller ID.")

    # Ensure compliance with applicable laws and regulations
    # All of the rules of TCPA apply even if a call is made by AI.
    # Do your own diligence for compliance.

    outbound_twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
    )

    call = client.calls.create(
        from_=PHONE_NUMBER_FROM, to=phone_number_to_call, twiml=outbound_twiml
    )

    await log_call_sid(call.sid)


async def log_call_sid(call_sid):
    """Log the call SID."""
    print(f"Call started with SID: {call_sid}")


async def generate_summary(transcript):
    """Generate a summary of the conversation using OpenAI."""
    full_text = "".join(transcript)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries of conversations. Focus on the key points discussed and any actions or conclusions reached.",
                },
                {
                    "role": "user",
                    "content": f"Please provide a summary of this conversation: {full_text}",
                },
            ],
            temperature=0.7,
            max_tokens=300,
        )

        summary = response.choices[0].message.content

        return {"transcript": full_text, "summary": summary}
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {"transcript": full_text, "summary": "Error generating summary"}


@app.post("/make-call")
async def create_call(call_request: CallRequest):
    global TOPIC
    try:
        # is_allowed = await check_number_allowed(call_request.phone_number)
        # if not is_allowed:
        #     return JSONResponse(
        #         status_code=400,
        #         content={"error": f"The number {call_request.phone_number} is not authorized"}
        #     )
        SYSTEM_MESSAGE = f"You are an AI voice assistant to ask the user questions and gather information about the topic of the call: {call_request.topic}"
        TOPIC = call_request.topic

        outbound_twiml = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response>"
            f"<Connect>"
            f'<Stream url="wss://{DOMAIN}/media-stream" />'
            f"</Connect>"
            f'<Hangup timeout="{call_request.max_duration}"/>'
            f"</Response>"
        )

        call = client.calls.create(
            from_=PHONE_NUMBER_FROM, to=call_request.phone_number, twiml=outbound_twiml
        )

        return JSONResponse(
            status_code=202,
            content={
                "message": "Call initiated",
                "call_sid": call.sid,
                "topic": call_request.topic,
            },
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# Add endpoint to get call summary
@app.get("/call-summary/{call_sid}")
async def get_call_summary(call_sid: str):
    if call_sid in call_summaries:
        return call_summaries[call_sid]
    return JSONResponse(
        status_code=404,
        content={"error": "Summary not found or call still in progress"},
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6060)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Run the Twilio AI voice assistant server."
#     )
#     parser.add_argument(
#         "--call",
#         required=True,
#         help="The phone number to call, e.g., '--call=+18005551212'",
#     )
#     args = parser.parse_args()

#     phone_number = args.call
#     print(
#         "Our recommendation is to always disclose the use of AI for outbound or inbound calls.\n"
#         "Reminder: All of the rules of TCPA apply even if a call is made by AI.\n"
#         "Check with your counsel for legal and compliance advice."
#     )

#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(make_call(phone_number))

#     uvicorn.run(app, host="0.0.0.0", port=PORT)

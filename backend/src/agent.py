import logging
import os

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
)
from livekit.plugins import google, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


SYSTEM_PROMPT = """
You are a friendly and efficient customer support agent for a tech company.

Your job is to help users with:
- Account issues
- Billing questions
- Product troubleshooting
- General customer support

Be concise, empathetic, friendly, and solution-oriented.

If you don't know something, say so honestly and offer to escalate the issue.

Speak naturally like a real customer support representative.
Do not use complex formatting, emojis, or symbols.

Keep your responses relatively short because you are a voice assistant.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Gemini Native Audio / Realtime model
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-latest",
            voice="Puck",
            api_key=os.getenv("GOOGLE_API_KEY"),
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],
    )

    # Start the agent session
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Connect to the LiveKit room
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
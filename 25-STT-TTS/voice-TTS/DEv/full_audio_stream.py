"""
Terminal Chat with Streaming LLM + Voice.ai TTS
Strategy:
  - Stream LLM tokens to terminal immediately (fast visual feedback)
  - Send FULL response text to TTS after streaming completes (clean audio)
  - For long responses, split into paragraph-sized chunks for TTS
"""

import io
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading

import requests
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()
# ── Config ────────────────────────────────────────────────────────────────────
VOICEAI_API_KEY = os.getenv("VOICE_API_KEY", "YOUR_VOICEAI_API_KEY")
VOICEAI_STREAM_URL = "https://dev.voice.ai/api/v1/tts/speech/stream"
VOICE_ID = None  # Optional: set your voice UUID here

# Max characters per TTS request (split long responses into chunks)
TTS_CHUNK_MAX_CHARS = 400


# ── Audio player detection ────────────────────────────────────────────────────

def get_player() -> str:
    for cmd in ("mpg123", "mpg321", "ffplay", "cvlc"):
        if shutil.which(cmd):
            return cmd
    if shutil.which("aplay") and shutil.which("ffmpeg"):
        return "aplay"
    try:
        import pygame
        pygame.mixer.init()
        return "pygame"
    except ImportError:
        pass
    return "file"


PLAYER = get_player()


# ── Audio playback ────────────────────────────────────────────────────────────

def play_audio(audio_bytes: bytes):
    if PLAYER == "pygame":
        import pygame
        pygame.mixer.music.load(io.BytesIO(audio_bytes))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    elif PLAYER in ("mpg123", "mpg321"):
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            subprocess.run([PLAYER, "-q", tmp], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            os.unlink(tmp)

    elif PLAYER == "ffplay":
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", tmp],
                check=True,
            )
        finally:
            os.unlink(tmp)

    elif PLAYER == "cvlc":
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            subprocess.run(["cvlc", "--play-and-exit", "-q", tmp], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        finally:
            os.unlink(tmp)

    elif PLAYER == "aplay":
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_mp3 = f.name
        tmp_wav = tmp_mp3.replace(".mp3", ".wav")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "quiet", "-i", tmp_mp3, tmp_wav], check=True)
            subprocess.run(["aplay", "-q", tmp_wav], check=True)
        except Exception as e:
            print(f"\n[Audio Error] {e}", file=sys.stderr)
        finally:
            for p in (tmp_mp3, tmp_wav):
                if os.path.exists(p):
                    os.unlink(p)
    else:
        _save_audio(audio_bytes)


_save_counter = 0

def _save_audio(audio_bytes: bytes):
    global _save_counter
    _save_counter += 1
    fname = f"output_{_save_counter}.mp3"
    with open(fname, "wb") as f:
        f.write(audio_bytes)
    print(f"\n[Audio saved → {fname}]")


# ── TTS ───────────────────────────────────────────────────────────────────────

def speak(text: str):
    """Send text to Voice.ai TTS and play the audio."""
    text = text.strip()
    if not text:
        return

    payload = {
        "text": text,
        "model": "voiceai-tts-v1-latest",
        "language": "en",
        "audio_format": "mp3",
    }
    if VOICE_ID:
        payload["voice_id"] = VOICE_ID

    try:
        response = requests.post(
            VOICEAI_STREAM_URL,
            headers={
                "Authorization": f"Bearer {VOICEAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            stream=True,
            timeout=30,
        )
        response.raise_for_status()

        audio_bytes = b"".join(
            chunk for chunk in response.iter_content(chunk_size=4096) if chunk
        )
        if audio_bytes:
            play_audio(audio_bytes)

    except requests.RequestException as e:
        print(f"\n[TTS Error] {e}", file=sys.stderr)


# ── Text chunker for long responses ──────────────────────────────────────────

def chunk_text(text: str, max_chars: int = TTS_CHUNK_MAX_CHARS) -> list[str]:
    """
    Split text into chunks at sentence boundaries, up to max_chars each.
    This keeps TTS context large enough for natural prosody while
    avoiding overly long API calls.
    """
    # Split on sentence endings
    sentence_re = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_re.split(text.strip())

    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence

    if current:
        chunks.append(current.strip())

    return chunks


# ── Background TTS worker ─────────────────────────────────────────────────────

_tts_queue: queue.Queue = queue.Queue()

def _tts_worker():
    while True:
        item = _tts_queue.get()
        if item is None:
            break
        speak(item)
        _tts_queue.task_done()

_tts_thread = threading.Thread(target=_tts_worker, daemon=True)
_tts_thread.start()


# ── LLM streaming ─────────────────────────────────────────────────────────────

model = ChatOpenAI(model="gpt-4o-mini", streaming=True)

def stream_response(messages) -> str:
    """
    Stream tokens to terminal for instant visual feedback.
    After streaming completes, split full response into TTS chunks and speak.
    """
    print("\nAssistant: ", end="", flush=True)

    full_text = ""
    for chunk in model.stream(messages):
        token = chunk.content
        if not token:
            continue
        print(token, end="", flush=True)
        full_text += token

    print()  # newline after response

    # Now speak the full response in well-sized chunks
    tts_chunks = chunk_text(full_text)
    for chunk in tts_chunks:
        _tts_queue.put(chunk)

    return full_text


# ── Main chat loop ────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Terminal Chat with Voice.ai TTS")
    print("  Type 'quit' or 'exit' to stop")
    print("=" * 60)

    if VOICEAI_API_KEY == "YOUR_VOICEAI_API_KEY":
        print("\n⚠️  Set VOICEAI_API_KEY env var for TTS.\n")

    if PLAYER == "file":
        print("⚠️  No audio player found. Install mpg123:")
        print("   sudo apt install mpg123\n")
    else:
        print(f"🔊 Audio player: {PLAYER}\n")

    conversation = [
        SystemMessage(content=(
            "You are a helpful assistant. "
            "Keep responses clear and natural for text-to-speech."
        )),
    ]

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        conversation.append(HumanMessage(content=user_input))
        response_text = stream_response(conversation)
        conversation.append(AIMessage(content=response_text))

        # Wait for all TTS to finish before showing next prompt
        _tts_queue.join()

    _tts_queue.put(None)
    _tts_thread.join(timeout=2)


if __name__ == "__main__":
    main()
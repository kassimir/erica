"""Optional STT/TTS hooks (placeholders; wire providers via config)."""

from __future__ import annotations

from typing import Protocol


class SpeechToText(Protocol):
    def transcribe(self, pcm_bytes: bytes) -> str: ...


class TextToSpeech(Protocol):
    def speak(self, text: str) -> None: ...


class NullSTT:
    def transcribe(self, pcm_bytes: bytes) -> str:
        return ""


class NullTTS:
    def speak(self, text: str) -> None:
        return None


stt: SpeechToText = NullSTT()
tts: TextToSpeech = NullTTS()

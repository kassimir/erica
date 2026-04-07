"""STT: SpeechRecognition + Google Web Speech API when optional deps are installed (WAV input)."""

from __future__ import annotations

import io
import logging
from typing import Protocol

log = logging.getLogger(__name__)


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


class SpeechRecognitionSTT:
    """Expects a valid WAV in `pcm_bytes` (browser/client must send WAV)."""

    def transcribe(self, pcm_bytes: bytes) -> str:
        import speech_recognition as sr

        r = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(pcm_bytes)) as source:
                audio = r.record(source)
        except Exception as e:
            log.warning("invalid audio: %s", e)
            return ""
        try:
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            log.warning("STT request failed: %s", e)
            return ""


def _make_stt() -> SpeechToText:
    try:
        import speech_recognition  # noqa: F401
    except ImportError:
        log.info("Optional STT: pip install erica-agent[voice] (SpeechRecognition)")
        return NullSTT()
    return SpeechRecognitionSTT()


stt: SpeechToText = _make_stt()
tts: TextToSpeech = NullTTS()

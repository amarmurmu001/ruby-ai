import threading
import logging
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr

logger = logging.getLogger("ruby.voice_listener")


class VoiceListener:
    SAMPLE_RATE = 16000
    SILENCE_THRESHOLD = 500
    SILENCE_DURATION = 1.2
    CHUNK_SECONDS = 0.1

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.available = self._check_mic()
        self._continuous_stop = threading.Event()
        self._record_stop = threading.Event()
        self._thread = None
        self._recording = []
        self._stream = None
        self._is_recording = False

    def _check_mic(self) -> bool:
        try:
            devices = sd.query_devices()
            return any(d["max_input_channels"] > 0 for d in devices)
        except Exception:
            return False

    def _rms(self, frame: np.ndarray) -> float:
        return float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))

    def listen_once(self, timeout: float = 10.0, phrase_limit: float = 15.0) -> str | None:
        if not self.available:
            logger.warning("No microphone available")
            return None

        logger.info("Recording...")
        self._recording = []
        self._is_recording = True
        self._record_stop.clear()
        silence_start = None

        def callback(indata, frames, t, status):
            if status:
                logger.debug("Stream status: %s", status)
            if not self._record_stop.is_set():
                self._recording.append(indata.copy())

        try:
            stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=1,
                dtype="int16",
                callback=callback,
            )
            stream.start()
        except Exception as e:
            logger.error("Failed to start audio stream: %s", e)
            self._is_recording = False
            return None

        start = time.time()
        while not self._record_stop.is_set() and time.time() - start < timeout:
            if len(self._recording) < 2:
                time.sleep(0.05)
                continue

            window = int(self.SILENCE_DURATION / self.CHUNK_SECONDS)
            recent = np.concatenate(self._recording[-window:], axis=0)
            level = self._rms(recent)
            elapsed = time.time() - start

            if level < self.SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > self.SILENCE_DURATION and elapsed > 1.5:
                    logger.info("Silence detected after %.1fs", elapsed)
                    break
            else:
                silence_start = None

            if elapsed >= phrase_limit:
                logger.info("Phrase limit reached")
                break

            time.sleep(0.05)

        stream.stop()
        stream.close()
        self._is_recording = False

        if len(self._recording) < 1:
            return None

        audio = np.concatenate(self._recording, axis=0)
        audio_bytes = audio.tobytes()
        audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)

        try:
            text = self.recognizer.recognize_google(audio_data)
            text = text.strip()
            logger.info("Heard: %s", text)
            return text if text else None
        except sr.UnknownValueError:
            logger.info("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error("Google STT request failed: %s", e)
            return None
        except Exception as e:
            logger.error("STT error: %s", e)
            return None

    def listen_stop(self):
        self._record_stop.set()
        logger.info("Recording stopped by user")

    def start_continuous(self, callback, wake_word: str = "ruby"):
        self._continuous_stop.clear()
        self._thread = threading.Thread(
            target=self._continuous_loop,
            args=(callback, wake_word.lower()),
            daemon=True,
        )
        self._thread.start()
        logger.info("Continuous listening started (wake: '%s')", wake_word)

    def _continuous_loop(self, callback, wake_word: str):
        chunk_duration = 1.5

        while not self._continuous_stop.is_set():
            n_samples = int(chunk_duration * self.SAMPLE_RATE)
            recording = sd.rec(n_samples, samplerate=self.SAMPLE_RATE,
                               channels=1, dtype="int16")

            deadline = time.time() + chunk_duration
            while time.time() < deadline:
                if self._continuous_stop.wait(0.2):
                    sd.stop()
                    logger.info("Wake loop stopped mid-chunk")
                    return

            audio_bytes = recording.tobytes()
            audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)

            try:
                text = self.recognizer.recognize_google(audio_data)
                text = text.strip().lower()
            except (sr.UnknownValueError, sr.RequestError):
                text = ""

            if text and wake_word in text:
                cmd = text.split(wake_word, 1)[-1].strip()
                logger.info("Wake word detected. Command: %s", cmd or "(none)")
                callback(cmd, via_wake=True)

    def stop(self):
        self._continuous_stop.set()
        self._record_stop.set()
        sd.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Listener stopped")

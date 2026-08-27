import math
import random
import wave
from array import array
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MUSIC_PATH = PROJECT_ROOT / "audio" / "generated" / "luxury_trap_rnb_96bpm.wav"


def generate_luxury_trap_rnb(output_path=DEFAULT_MUSIC_PATH, duration_seconds=10.0, sample_rate=44100):
    """Generate an original instrumental beat without sampled recordings."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(duration_seconds * sample_rate)
    beat_seconds = 60.0 / 96.0
    rng = random.Random(20260803)
    samples = array("h")

    for index in range(frame_count):
        t = index / sample_rate
        beat_position = (t % beat_seconds) / beat_seconds
        half_beat = (t % (beat_seconds / 2)) / (beat_seconds / 2)
        chord_step = int(t / (beat_seconds * 2)) % 4
        root = (55.0, 65.41, 73.42, 61.74)[chord_step]

        pad = sum(math.sin(2 * math.pi * root * ratio * t) for ratio in (1.0, 1.5, 2.0)) * 0.055
        bass = math.sin(2 * math.pi * root * t) * 0.24 * math.exp(-5.0 * beat_position)
        kick = math.sin(2 * math.pi * (62 - 25 * beat_position) * t) * 0.55 * math.exp(-18 * beat_position)
        clap_position = ((t - beat_seconds) % (beat_seconds * 2)) / (beat_seconds * 2)
        clap = (rng.random() * 2 - 1) * 0.25 * math.exp(-45 * clap_position) if clap_position < 0.18 else 0.0
        hat = (rng.random() * 2 - 1) * 0.08 * math.exp(-55 * half_beat)
        fade = min(t / 0.35, 1.0, max((duration_seconds - t) / 0.55, 0.0))
        value = max(-1.0, min(1.0, (pad + bass + kick + clap + hat) * fade))
        pcm = int(value * 32767)
        samples.extend((pcm, pcm))

    with wave.open(str(output_path), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(samples.tobytes())
    return output_path.resolve()


def ensure_default_music_track():
    if not DEFAULT_MUSIC_PATH.is_file():
        return generate_luxury_trap_rnb()
    return DEFAULT_MUSIC_PATH.resolve()

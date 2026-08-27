import wave

from core.music_generator import generate_luxury_trap_rnb


def test_generates_original_stereo_music_track(tmp_path):
    output = generate_luxury_trap_rnb(tmp_path / "beat.wav", duration_seconds=1.0)
    with wave.open(str(output), "rb") as audio:
        assert audio.getnchannels() == 2
        assert audio.getframerate() == 44100
        assert 0.99 <= audio.getnframes() / audio.getframerate() <= 1.01

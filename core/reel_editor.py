import subprocess
from pathlib import Path

import imageio_ffmpeg

from core.media_database import DB_FILE, add_media, load_database, update_media
from core.music_generator import ensure_default_music_track


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REELS_DIR = PROJECT_ROOT / "videos" / "processed"
TARGET_SECONDS = 10.0


def probe_video(video_path: Path) -> dict:
    frames = imageio_ffmpeg.read_frames(str(video_path), pix_fmt="rgb24")
    try:
        metadata = next(frames)
    finally:
        frames.close()
    return {
        "duration": float(metadata.get("duration") or 0),
        "fps": float(metadata.get("fps") or 0),
        "size": metadata.get("size"),
        "codec": metadata.get("codec"),
    }


def get_video_edit_queue(db_file=DB_FILE) -> list[dict]:
    return [
        item
        for item in load_database(db_file)
        if item.get("type") == "video"
        and item.get("status") == "pending_video_edit"
        and item.get("queue") == "video_edit_10s"
    ]


def edit_reel(video_path: Path, output_dir=REELS_DIR, target_seconds=TARGET_SECONDS, music_path=None) -> dict:
    video_path = Path(video_path).resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    metadata = probe_video(video_path)
    duration = metadata["duration"]
    if duration <= 0:
        raise ValueError(f"Could not read video duration: {video_path.name}")

    if music_path is None:
        raise ValueError("A licensed music track is required. Source video audio is never used.")
    music_path = Path(music_path).resolve()
    if not music_path.is_file():
        raise FileNotFoundError(f"Music not found: {music_path}")

    clip_duration = min(float(target_seconds), duration)
    start_at = max((duration - clip_duration) / 2, 0)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_path.stem}_reel_10s.mp4"

    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-ss", f"{start_at:.3f}",
        "-i", str(video_path),
    ]
    command.extend(["-i", str(music_path)])
    command.extend([
        "-t", f"{clip_duration:.3f}",
        "-map_metadata", "0",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
    ])
    command.extend([
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-af", f"afade=t=in:st=0:d=0.25,afade=t=out:st={max(clip_duration - 0.5, 0):.3f}:d=0.5,volume=0.82",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
    ])
    command.extend(["-movflags", "+faststart", str(output_path)])
    subprocess.run(command, check=True, capture_output=True, text=True)

    result_metadata = probe_video(output_path)
    return {
        "source_path": str(video_path),
        "output_path": str(output_path.resolve()),
        "source_duration": round(duration, 3),
        "reel_duration": round(result_metadata["duration"], 3),
        "clip_start": round(start_at, 3),
        "source_size": metadata["size"],
        "output_size": result_metadata["size"],
        "source_audio_muted": True,
        "music_status": "licensed_music_added",
        "music_path": str(music_path),
    }


def create_reel_from_photos(
    photo_paths: list[Path],
    output_path: Path,
    *,
    music_path: Path,
    music_start_seconds=0,
    target_seconds=TARGET_SECONDS,
) -> dict:
    """Create a vertical Reel from real photos, with no camera audio."""
    photos = [Path(path).resolve() for path in photo_paths]
    if not photos:
        raise ValueError("At least one real photo is required to create a photo Reel.")
    missing = [path for path in photos if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Photo not found: {missing[0]}")

    music_path = Path(music_path).resolve()
    if not music_path.is_file():
        raise FileNotFoundError(f"Music not found: {music_path}")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    segment_seconds = float(target_seconds) / len(photos)
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y"]
    for photo in photos:
        command.extend(["-loop", "1", "-t", f"{segment_seconds:.3f}", "-i", str(photo)])
    command.extend([
        "-stream_loop", "-1",
        "-ss", f"{float(music_start_seconds):.3f}",
        "-i", str(music_path),
    ])

    filters = []
    video_inputs = []
    fade_out_at = max(segment_seconds - 0.35, 0)
    for index in range(len(photos)):
        filters.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "zoompan=z='min(max(zoom,pzoom)+0.00035,1.08)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
            f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_at:.3f}:d=0.35,"
            f"trim=duration={segment_seconds:.3f},setpts=PTS-STARTPTS[v{index}]"
        )
        video_inputs.append(f"[v{index}]")
    filters.append(
        f"{''.join(video_inputs)}concat=n={len(photos)}:v=1:a=0,"
        f"tpad=stop_mode=clone:stop_duration={float(target_seconds):.3f},"
        f"trim=duration={float(target_seconds):.3f},setpts=PTS-STARTPTS[vout]"
    )

    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[vout]",
        "-map", f"{len(photos)}:a:0",
        "-t", f"{float(target_seconds):.3f}",
        "-af", f"afade=t=in:st=0:d=0.25,afade=t=out:st={max(float(target_seconds) - 0.5, 0):.3f}:d=0.5,volume=0.82",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ])
    subprocess.run(command, check=True, capture_output=True, text=True)
    metadata = probe_video(output_path)
    return {
        "output_path": str(output_path),
        "reel_duration": round(metadata["duration"], 3),
        "output_size": metadata["size"],
        "source_photos": [str(path) for path in photos],
        "source_audio_muted": True,
        "music_status": "licensed_music_added",
        "music_path": str(music_path),
        "creation_method": "image_montage",
    }


def create_daily_ai_reel_if_needed(
    db_file=DB_FILE,
    output_dir=REELS_DIR,
    now=None,
    image_generator=None,
) -> dict | None:
    """Generate fresh AI nail scenes and make today's Reel when no video exists."""
    from datetime import datetime

    current = now or datetime.now()
    database = load_database(db_file)
    active_video_statuses = {
        "pending_video_edit", "reel_ready", "reel_draft_ready", "approved", "scheduled"
    }
    if any(item.get("type") == "video" and item.get("status") in active_video_statuses for item in database):
        return None

    if image_generator is None:
        from agents.image_generator_agent import ImageGeneratorAgent

        agent = ImageGeneratorAgent()
        image_generator = agent.run

    prompts = (
        "Photorealistic luxury nail editorial, elegant hand with glossy nude gold nails, upscale fashion lighting, vertical composition, no text, no watermark.",
        "Photorealistic pink luxury chrome nail design, elegant hand, premium salon campaign, soft glamorous lighting, vertical composition, no text, no watermark.",
        "Photorealistic cat-eye gemstone nails, elegant hand, dark luxury ambient background, high-end beauty advertising, vertical composition, no text, no watermark.",
    )
    generated_images = [Path(image_generator(prompt)).resolve() for prompt in prompts]
    file_name = f"daily_ai_reel_{current:%Y%m%d}.mp4"
    output_path = Path(output_dir) / file_name
    from core.music_library import select_vocal_music_track

    music = select_vocal_music_track()
    reel = create_reel_from_photos(
        generated_images,
        output_path,
        music_path=Path(music["path"]),
        music_start_seconds=music.get("hook_start_seconds", 0),
    )
    reel.update({
        "creation_method": "ai_image_montage",
        "ai_image_generated": True,
        "music_title": music.get("title"),
        "music_artist": music.get("artist"),
        "music_source": music.get("source"),
    })
    add_media(
        file_name,
        "video",
        str(output_path.resolve()),
        db_file=db_file,
        status="reel_ready",
        queue="reel_content_generation",
        reel_path=str(output_path.resolve()),
        video_edit=reel,
        generated_from_ai_images=True,
        ai_image_generated=True,
    )
    return {"file": file_name, "status": "reel_ready", **reel}


def process_video_queue(db_file=DB_FILE, output_dir=REELS_DIR) -> list[dict]:
    results = []
    for media in get_video_edit_queue(db_file):
        try:
            reel = edit_reel(
                Path(media["path"]),
                output_dir=output_dir,
                music_path=ensure_default_music_track(),
            )
        except Exception as exc:
            update_media(
                media["file"],
                db_file=db_file,
                status="video_edit_failed",
                queue="video_edit_retry",
                video_edit_error_type=exc.__class__.__name__,
            )
            results.append({"file": media["file"], "status": "video_edit_failed"})
            continue

        update_media(
            media["file"],
            db_file=db_file,
            status="reel_ready",
            queue="reel_content_generation",
            reel_path=reel["output_path"],
            video_edit=reel,
        )
        results.append({"file": media["file"], "status": "reel_ready", **reel})
    return results


if __name__ == "__main__":
    results = process_video_queue()
    if not results:
        print("No videos are waiting for Reel editing.")
    for result in results:
        print(f"{result['file']} -> {result['status']}")

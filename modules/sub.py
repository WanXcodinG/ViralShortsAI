import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import json
import re
import streamlit as st
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Regex pattern to match lines like:
# [HH:MM.SSS --> HH:MM.SSS] text (confidence)
LINE_PATTERN = re.compile(
    r'^\[(\d+):(\d+\.\d+)\s*-->\s*(\d+):(\d+\.\d+)\]\s*(.*?)\s*\(([\d.]+)\)$'
)

def time_to_ms(minutes_str, seconds_str):
    """Convert MM and SSS to total milliseconds."""
    minutes = int(minutes_str)
    seconds = float(seconds_str)
    total_seconds = minutes * 60 + seconds
    return int(total_seconds * 1000)

def extract_audio(video_file: Path, out_wav: Path):
    """Extract audio from video using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-i", str(video_file),
        "-ar", "16000",
        "-ac", "1",
        str(out_wav),
        "-y"
    ]
    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info(f"FFmpeg output: {result.stdout.decode('utf-8', errors='ignore')}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore')
        logger.error(f"FFmpeg error while extracting audio from {video_file}: {error_msg}")
        raise RuntimeError(f"FFmpeg error while extracting audio: {error_msg}")

def process_audio(wav_file: Path, model_path: Path):
    """Transcribe audio using whisper.cpp and extract token-level data."""
    main_binary = Path.cwd() / "modules" / "whisper.cpp" / "main"
    model = Path.cwd() / "modules" / "models" / "ggml-medium.en.bin"

    if not main_binary.exists():
        raise FileNotFoundError(f"Main binary not found: {main_binary}")
    if not model.exists():
        raise FileNotFoundError(f"Model file not found: {model}")
    if not wav_file.exists():
        raise FileNotFoundError(f"WAV file not found: {wav_file}")

    full_command = [
        str(main_binary),
        "-m", str(model),
        "-f", str(wav_file),
        "--output-json"
    ]

    st.write(f"Running Whisper command: {' '.join(full_command)}")
    try:
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if process.returncode != 0:
            error_msg = error.decode('utf-8', errors='ignore')
            logger.error(f"Whisper.cpp error: {error_msg}")
            raise RuntimeError(f"Error processing audio: {error_msg}")

        decoded_str = output.decode('utf-8', errors='ignore').strip()

        # Parse token-level timestamps from the output lines
        captions = []
        lines = decoded_str.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = LINE_PATTERN.match(line)
            if match:
                start_min, start_sec, end_min, end_sec, token_text, confidence_str = match.groups()
                start_ms = time_to_ms(start_min, start_sec)
                end_ms = time_to_ms(end_min, end_sec)
                confidence = float(confidence_str)

                duration = end_ms - start_ms
                captions.append({
                    "text": token_text,
                    "startMs": 0,
                    "endMs": duration,
                    "timestampMs": start_ms,
                    "confidence": confidence
                })

        return captions

    except Exception as e:
        logger.error(f"Error running Whisper.cpp: {e}")
        raise RuntimeError(f"Error running Whisper.cpp: {e}")

def save_transcription_as_json(captions, out_path: Path):
    """Save the transcription data to a JSON file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2)
        logger.info(f"Saved transcription JSON to {out_path}")

import os

def process_video(video_file: Path, model_path: Path):
    """Process the video file to extract and transcribe audio."""
    audio_output_dir = Path.cwd() / "media" / "audio"
    audio_output_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    output_audio_path = audio_output_dir / f"{video_file.stem}.wav"
    out_json = Path.cwd() / "media" / "subs" / f"{video_file.stem}.json"

    try:
        # Extract audio
        logger.info(f"Extracting audio from {video_file}")
        cmd = [
            "ffmpeg",
            "-i", str(video_file),
            "-ar", "16000",
            "-ac", "1",
            str(output_audio_path),
            "-y"
        ]
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Verify audio extraction
        if not output_audio_path.exists():
            raise FileNotFoundError(f"Audio file not created: {output_audio_path}")

        # Transcribe audio
        logger.info(f"Transcribing {output_audio_path}")
        captions = process_audio(output_audio_path, model_path)

        # Handle empty transcriptions
        if not captions:
            logger.warning(f"No transcription generated for {video_file}")
            raise ValueError(f"Empty transcription for {video_file}")

        # Save transcription
        save_transcription_as_json(captions, out_json)
        logger.info(f"Saved transcription to {out_json}")
    except Exception as e:
        logger.error(f"Error processing {video_file}: {e}")
        raise RuntimeError(f"Error processing {video_file}: {e}")
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transcribe video to JSON with token-level timestamps.")
    parser.add_argument("video_file", type=Path, help="Path to the video file.")
    parser.add_argument("model_path", type=Path, help="Path to the whisper.cpp model directory.")
    args = parser.parse_args()

    process_video(args.video_file, args.model_path)
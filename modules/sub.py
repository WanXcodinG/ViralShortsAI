import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import json
import os
import streamlit as st

logger = logging.getLogger(__name__)

def extract_audio(video_file: Path, out_wav: Path):
    """
    Extracts audio from a video file and converts it to WAV format.

    Args:
        video_file (Path): Path to the input video file.
        out_wav (Path): Path to the output WAV file.

    Raises:
        RuntimeError: If FFmpeg encounters an error during processing.
    """
    cmd = [
        "ffmpeg",
        "-i", str(video_file),
        "-ar", "16000",
        "-ac", "1",  # Ensure mono audio
        str(out_wav),
        "-y"
    ]
    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info(f"FFmpeg output: {result.stdout.decode('utf-8')}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8')
        logger.error(f"FFmpeg error while extracting audio from {video_file}: {error_msg}")
        st.write(f"FFmpeg error: {error_msg}")
        raise RuntimeError(f"FFmpeg error while extracting audio: {error_msg}")

def save_transcription_as_json(transcription: str, out_path: Path):
    """
    Saves the transcription result to a JSON file.

    Args:
        transcription (str): The transcription text.
        out_path (Path): Path to the output JSON file.
    """
    captions = [{"text": transcription}]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2)
        logger.info(f"Saved transcription JSON to {out_path}")
        st.write(f"Dumping transcription to {out_path}")

def process_audio(wav_file, model_name="medium.en"):
    """
    Processes audio using whisper.cpp.

    Args:
        wav_file (str): Path to the WAV file.
        model_name (str): Name of the Whisper model to use.

    Returns:
        str: The processed transcription.

    Raises:
        RuntimeError: If whisper.cpp encounters an error.
    """
    main_binary = Path(__file__).parent / "whisper.cpp" / "main"
    main_binary = main_binary.resolve()
    model = Path(__file__).parent / "models" / f"ggml-{model_name}.bin"
    model = model.resolve()

    if not main_binary.exists():
        st.write(f"Main binary not found: {main_binary}")
        raise FileNotFoundError(f"Main binary not found: {main_binary}")
    if not model.exists():
        st.write(f"Model file not found: {model}")
        raise FileNotFoundError(f"Model file not found: {model}")
    if not os.path.exists(wav_file):
        st.write(f"WAV file not found: {wav_file}")
        raise FileNotFoundError(f"WAV file not found: {wav_file}")

    full_command = [
        str(main_binary),
        "-m", str(model),
        "-f", str(wav_file),
        "-nt"
    ]

    logger.info(f"Running Whisper command: {' '.join(full_command)}")
    try:
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()

        if process.returncode != 0:
            error_msg = error.decode('utf-8')
            logger.error(f"Whisper.cpp error: {error_msg}")
            st.write(f"Whisper error: {error_msg}")
            raise RuntimeError(f"Error processing audio: {error_msg}")

        decoded_str = output.decode('utf-8').strip()
        processed_str = decoded_str.replace('[BLANK_AUDIO]', '').strip()
        return processed_str
    except Exception as e:
        logger.error(f"Error running Whisper.cpp: {e}")
        raise RuntimeError(f"Error running Whisper.cpp: {e}")

def process_video(video_file: Path):
    """
    Processes a video file to extract audio, transcribe it, and save the results.

    Args:
        video_file (Path): Path to the video file.

    Raises:
        Exception: If any part of the process fails.
    """
    with TemporaryDirectory() as temp_dir:
        temp_wav = Path(temp_dir) / f"{video_file.stem}.wav"
        out_json = Path.cwd() / "media" / "subs" / f"{video_file.stem}.json"
        try:
            logger.info(f"Extracting audio from {video_file}")
            st.write(f"Extracting audio from {video_file}")
            extract_audio(video_file, temp_wav)

            logger.info(f"Transcribing {temp_wav}")
            st.write(f"Transcribing {temp_wav}")
            transcription = process_audio(str(temp_wav))
            
            if not transcription.strip():
                logger.warning(f"No transcription generated for {video_file}")
                raise ValueError(f"Empty transcription for {video_file}")

            save_transcription_as_json(transcription, out_json)
            logger.info(f"Saved transcription to {out_json}")
        except Exception as e:
            logger.error(f"Error processing {video_file}: {e}")
            st.write(f"Error processing {video_file}: {e}")
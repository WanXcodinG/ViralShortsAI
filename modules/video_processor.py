import subprocess
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip
from modules.silence_trimmer import SilenceTrimmer
from modules.zoom_effect_creator import create_zoom_effects
from modules.broller import insert_broll
from modules.silence import detect_silence
from modules.sub import process_video
import streamlit as st
import subprocess
import os

from modules.zoomer import add_zoom_effects_from_json

def render_remotion_video():
    try:
        result = subprocess.run(['node', 'render.js'], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")

def process_with_node(directory_or_file):
    """
    Run the sub.mjs file using Node.js with the provided directory or file as input.

    Args:
        directory_or_file (str): The path to the video file or directory to process.
    """
    node_script_path = os.path.join(os.getcwd(), "sub.mjs")

    if not os.path.exists(node_script_path):
        raise FileNotFoundError(f"Node.js script not found at {node_script_path}")

    try:
        # Call the Node.js script
        subprocess.run(
            ["node", node_script_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(f"Successfully processed: {directory_or_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while processing {directory_or_file}:\n{e.stderr}")

def process_videos(media_dir: Path, output_dir: Path, broll_suggestions, voiceover_path: Path):
    video_files = list((media_dir / "videos").glob("*.mp4"))
    final_paths = []

    for video_file in video_files:
        # Run silence detection if needed
        silence_json_path = output_dir / "silence.json"
        video_transcript_file = output_dir / f"{video_file.stem}.json"
        detect_silence(video_transcript_file, silence_json_path)
        st.write(f"Detected silence for {video_file.name}")
        # Remove silence
        trimmed_path = output_dir / f"trimmed_{video_file.name}"
        trimmer = SilenceTrimmer(str(video_file), str(silence_json_path), str(trimmed_path))

        trimmer.trim_video()
        
        transcript_path = Path.cwd() / "media" / "subs" / f"trimmed_{video_file.stem}.json"

        # Add captions
        process_with_node(Path.cwd() / "media" / "videos")
        # Create zoom effects
        zoom_effects_path = output_dir / "zoom_effects.json"
        # Integrate transcript JSON created by sub.mjs or another step.
        # Assume transcript_path points to a JSON transcript used by create_zoom_effects
        create_zoom_effects(str(transcript_path), str(zoom_effects_path))
        add_zoom_effects_from_json(str(trimmed_path), str(zoom_effects_path), str(trimmed_path))
        # Insert B-roll
        current_broll = []
        for suggestion in broll_suggestions:
            if suggestion["filename"] == video_file.name:
                current_broll = suggestion["suggested_broll"]
                st.write(f"Inserting B-roll for {video_file.name}")
                break
            else:
                st.warning(f"No B-roll suggestions found for {video_file.name}")
        final_video_path = output_dir / f"final_{video_file.stem}.mp4"
        insert_broll(str(trimmed_path), current_broll, final_video_path)
        final_paths.append(final_video_path)

    # Merge with voiceover
    if final_paths:
        main_clip = VideoFileClip(str(final_paths[0]))
       # voiceover = AudioFileClip(str(voiceover_path))
       # final_clip = main_clip.set_audio(voiceover)
        final_output_path = output_dir / 'final_video.mp4'
        main_clip.write_videofile(str(final_output_path.stem) + ".mp4", codec='libx264', audio_codec='aac')
        return final_output_path
    else:
        raise Exception("No final videos produced.")
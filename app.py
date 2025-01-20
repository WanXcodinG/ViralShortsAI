import streamlit as st
from pathlib import Path
import shutil
import subprocess
import os
import atexit
import openai
from modules.config import get_openai_api_key, get_elevenlabs_api_key
from modules.directory_reader import gather_media_files
from modules.media_analyzer import analyze_media_files
from modules.broll_suggester import suggest_broll
from modules.voiceover_generator import generate_voiceover
from modules.video_processor import process_videos

# Path to the sub_v1.mjs script
SUB_SCRIPT_PATH = "/Users/andreas/Desktop/ViralShortAI/viralshortai/js-scripts/sub_v1.mjs"
NODE_EXECUTABLE = "node"  # Ensure Node.js is installed and accessible

# Subprocess handle for managing sub_v1.mjs
subprocess_handle = None

def start_sub_v1_script():
    """Start the sub_v1.mjs script as a subprocess."""
    global subprocess_handle
    if not subprocess_handle:
        subprocess_handle = subprocess.Popen(
            [NODE_EXECUTABLE, SUB_SCRIPT_PATH],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        st.write("sub_v1.mjs started.")

def stop_sub_v1_script():
    """Stop the sub_v1.mjs subprocess."""
    global subprocess_handle
    if subprocess_handle:
        subprocess_handle.terminate()
        try:
            subprocess_handle.wait(timeout=5)
        except subprocess.TimeoutExpired:
            subprocess_handle.kill()  # Force kill if not terminated
        st.write("sub_v1.mjs stopped.")
        subprocess_handle = None

# Ensure the script is stopped when the app exits
atexit.register(stop_sub_v1_script)

def main():
    st.title("Viral Short AI - Automated Video Generation")

    # Start the sub_v1.mjs script
    start_sub_v1_script()

    # Set up API keys
    openai.api_key = get_openai_api_key()
    eleven_api_key = get_elevenlabs_api_key()

    # Define paths
    project_root = Path(__file__).parent
    media_dir = project_root / 'media'
    context_path = project_root / 'context' / 'marketing.md'
    output_dir = project_root / 'js-scripts' / 'public'
    output_dir.mkdir(exist_ok=True)

    # Read context
    marketing_context = context_path.read_text()

    # Gather media files
    media_files = gather_media_files(media_dir)
    analyzed_media = analyze_media_files(media_files, marketing_context)
    st.json([m.dict() for m in analyzed_media])

    # Suggest B-roll
    broll_suggestions = suggest_broll(analyzed_media, marketing_context)
    st.json(broll_suggestions)

    # Generate voiceover
    voiceover_text = "Your synthesized voiceover text based on marketing context."
    voiceover_path = output_dir / 'voiceover.mp3'
    # generate_voiceover(voiceover_text, voiceover_path, eleven_api_key)
    # st.audio(str(voiceover_path))

    # Process Videos (includes silence trimming, captions from sub.mjs, zoom effects from AI)
    final_video_path = process_videos(
        media_dir,
        output_dir,
        broll_suggestions,
        voiceover_path
    )

    # Move the video to the 'js-scripts/public' directory
    destination_path = output_dir / final_video_path.name
    shutil.move(str(final_video_path), str(destination_path))

    st.write(f"Generated video path: {final_video_path}")
    root_video_path = project_root / "final_video.mp4"
    destination_path = output_dir / "final_video.mp4"

    if root_video_path.exists():
        shutil.move(str(root_video_path), str(destination_path))
        st.video(str(destination_path))
        st.success("Video moved successfully.")
    else:
        st.error(f"Generated video not found in project root: {root_video_path}")

if __name__ == "__main__":
    main()
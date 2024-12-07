import streamlit as st
from pathlib import Path
import os
import openai
from modules.config import get_openai_api_key, get_elevenlabs_api_key
from modules.directory_reader import gather_media_files
from modules.media_analyzer import analyze_media_files
from modules.broll_suggester import suggest_broll
from modules.voiceover_generator import generate_voiceover
from modules.video_processor import process_videos

def main():
    st.title("Viral Short AI - Automated Video Generation")
    
    openai.api_key = get_openai_api_key()
    eleven_api_key = get_elevenlabs_api_key()

    project_root = Path(__file__).parent
    media_dir = project_root / 'media'
    context_path = project_root / 'context' / 'marketing.md'
    output_dir = project_root / 'out'
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

    st.video(str(final_video_path))
    st.success("Video processing complete.")

if __name__ == "__main__":
    main()
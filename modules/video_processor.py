import subprocess
from pathlib import Path
import os
import time
import shutil
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from modules.silence_trimmer import SilenceTrimmer
from modules.zoom_effect_creator import create_zoom_effects
from modules.broller import insert_broll
from modules.silence import detect_silence
from modules.sub import process_video
import streamlit as st
import subprocess
import traceback

from modules.zoomer import add_zoom_effects_from_json

def render_remotion_video():
    """Render a video using Remotion."""
    try:
        result = subprocess.run(['node', 'render.js'], check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Remotion rendering error: {e.stderr}")
        return False
    except Exception as e:
        st.error(f"Unexpected error during Remotion rendering: {str(e)}")
        return False

def process_with_node(directory_or_file):
    """
    Run the sub.mjs file using Node.js with the provided directory or file as input.

    Args:
        directory_or_file (str): The path to the video file or directory to process.
    """
    node_script_path = os.path.join(os.getcwd(), "sub.mjs")

    if not os.path.exists(node_script_path):
        st.warning(f"Node.js script not found at {node_script_path}. Falling back to simpler processing.")
        return False

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
        return True
    except subprocess.CalledProcessError as e:
        st.warning(f"Error occurred while processing {directory_or_file} with Node.js:\n{e.stderr}")
        return False
    except Exception as e:
        st.warning(f"Unexpected error running Node.js script: {str(e)}")
        return False

def create_simple_caption(video_path, output_path):
    """
    Create a simple caption for a video when the Node.js script fails.
    Uses basic video properties for the caption.
    """
    try:
        # Use moviepy to add a simple caption
        video = VideoFileClip(str(video_path))
        
        # Generate a simple caption with the video name
        video_name = Path(video_path).stem.replace('_', ' ').title()
        text_clip = TextClip(f"{video_name}", fontsize=24, color='white', 
                          bg_color='black', font='Arial-Bold', 
                          method='caption', size=(video.w, None))
        
        # Position at the bottom
        text_clip = text_clip.set_position(('center', 'bottom')).set_duration(video.duration)
        
        # Composite
        final = CompositeVideoClip([video, text_clip])
        
        # Write to file
        final.write_videofile(str(output_path), codec='libx264', audio_codec='aac')
        return True
    except Exception as e:
        print(f"Error creating simple caption: {e}")
        # Just copy the original file as fallback
        shutil.copy(str(video_path), str(output_path))
        return False

def process_videos(media_dir: Path, output_dir: Path, broll_suggestions, voiceover_path: Path):
    """
    Process videos with B-roll, captions, and effects.
    
    Args:
        media_dir: Directory containing media files
        output_dir: Directory for output files
        broll_suggestions: Suggestions for B-roll overlays
        voiceover_path: Path to the voiceover audio file
    
    Returns:
        Path to the final video
    """
    # Create a videos directory if it doesn't exist
    videos_dir = media_dir / "videos"
    if not videos_dir.exists():
        videos_dir.mkdir(parents=True, exist_ok=True)
        st.warning("Created videos directory, but no videos were found.")
        
    # Find video files
    video_files = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.mov"))
    if not video_files:
        st.error("No video files found in the videos directory.")
        return create_empty_video(output_dir)
    
    # Process each video
    final_paths = []
    for video_file in video_files:
        try:
            st.info(f"Processing video: {video_file.name}")
            
            # Create a subdirectory for intermediate files
            video_temp_dir = output_dir / video_file.stem
            video_temp_dir.mkdir(exist_ok=True)
            
            # Run silence detection
            silence_json_path = video_temp_dir / "silence.json"
            video_transcript_file = videos_dir / f"{video_file.stem}.json"
            silence_detected = False
            
            try:
                detect_silence(video_transcript_file, silence_json_path)
                silence_detected = True
                st.success(f"Detected silence for {video_file.name}")
            except Exception as e:
                st.warning(f"Silence detection failed for {video_file.name}: {str(e)}")
            
            # Remove silence if detected
            trimmed_path = video_temp_dir / f"trimmed_{video_file.name}"
            if silence_detected and silence_json_path.exists():
                try:
                    trimmer = SilenceTrimmer(str(video_file), str(silence_json_path), str(trimmed_path))
                    trimmer.trim_video()
                    st.success(f"Trimmed silence from {video_file.name}")
                except Exception as e:
                    st.warning(f"Error trimming silence: {str(e)}")
                    # Copy the original file as fallback
                    shutil.copy(str(video_file), str(trimmed_path))
            else:
                # If silence detection failed, just copy the original file
                shutil.copy(str(video_file), str(trimmed_path))
            
            # Ensure the subs directory exists
            subs_dir = media_dir / "subs"
            subs_dir.mkdir(exist_ok=True)
            
            # Add captions with Node.js
            captioning_success = process_with_node(str(videos_dir))
            
            # Look for transcript JSON file
            transcript_path = subs_dir / f"trimmed_{video_file.stem}.json"
            if not transcript_path.exists():
                transcript_path = subs_dir / f"{video_file.stem}.json"
            
            # Create zoom effects if possible
            zoom_effects_path = video_temp_dir / "zoom_effects.json"
            
            try:
                if transcript_path.exists():
                    create_zoom_effects(str(transcript_path), str(zoom_effects_path))
                    add_zoom_effects_from_json(str(trimmed_path), str(zoom_effects_path), str(trimmed_path))
                    st.success(f"Added zoom effects to {video_file.name}")
                else:
                    st.warning(f"No transcript found for zoom effects: {video_file.name}")
            except Exception as e:
                st.warning(f"Error adding zoom effects: {str(e)}")
            
            # Insert B-roll
            current_broll = []
            for suggestion in broll_suggestions:
                if suggestion["filename"] == video_file.name:
                    current_broll = suggestion["suggested_broll"]
                    st.success(f"Found B-roll suggestions for {video_file.name}")
                    break
            
            final_video_path = video_temp_dir / f"final_{video_file.stem}.mp4"
            
            try:
                if current_broll:
                    insert_broll(str(trimmed_path), current_broll, final_video_path)
                    st.success(f"Inserted B-roll into {video_file.name}")
                else:
                    # Just copy the file if no B-roll
                    shutil.copy(str(trimmed_path), str(final_video_path))
            except Exception as e:
                st.warning(f"Error inserting B-roll: {str(e)}")
                # Use the trimmed video as fallback
                shutil.copy(str(trimmed_path), str(final_video_path))
            
            final_paths.append(final_video_path)
            
        except Exception as e:
            st.error(f"Error processing video {video_file.name}: {str(e)}")
            traceback.print_exc()
            continue

    # If no videos were successfully processed, create an empty one
    if not final_paths:
        st.warning("No videos were successfully processed. Creating a placeholder video.")
        return create_empty_video(output_dir)

    # Merge with voiceover if available
    try:
        if len(final_paths) > 0:
            main_clip = VideoFileClip(str(final_paths[0]))
            
            # Add voiceover if it exists
            if voiceover_path.exists() and os.path.getsize(str(voiceover_path)) > 0:
                try:
                    voiceover = AudioFileClip(str(voiceover_path))
                    main_clip = main_clip.set_audio(voiceover)
                    st.success("Added voiceover to the video")
                except Exception as e:
                    st.warning(f"Error adding voiceover: {str(e)}")
            
            final_output_path = output_dir / 'final_video.mp4'
            main_clip.write_videofile(str(final_output_path), codec='libx264', audio_codec='aac')
            return final_output_path
        else:
            raise Exception("No final videos produced.")
    except Exception as e:
        st.error(f"Error in final video production: {str(e)}")
        return create_empty_video(output_dir)

def create_empty_video(output_dir: Path):
    """
    Create a simple placeholder video when no videos could be processed.
    """
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        # Create a blank background
        color_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=10)
        
        # Add text
        text_clip = TextClip("No videos were successfully processed", 
                           fontsize=50, color='white', font='Arial-Bold',
                           size=(1000, None))
        text_clip = text_clip.set_position('center').set_duration(10)
        
        # Combine
        final_clip = CompositeVideoClip([color_clip, text_clip])
        
        # Write to file
        final_output_path = output_dir / 'final_video.mp4'
        final_clip.write_videofile(str(final_output_path), codec='libx264', fps=24)
        
        return final_output_path
    except Exception as e:
        st.error(f"Error creating placeholder video: {str(e)}")
        
        # Last resort: create an empty file
        final_output_path = output_dir / 'final_video.mp4'
        with open(final_output_path, 'wb') as f:
            f.write(b'')
        
        return final_output_path
from typing import List
from pathlib import Path
import moviepy.editor as mp
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import streamlit as st
from PIL import Image

def insert_broll(main_video_path: str, broll_paths: List[dict], output_path: str, image_duration: int = 5):
    """
    Overlays B-roll (videos or images) onto the main video while keeping the main video's audio.

    Args:
        main_video_path (str): Path to the main video file.
        broll_paths (List[dict]): List of dictionaries with B-roll metadata (path, timestamp, duration).
        output_path (str): Path to save the final video.
        image_duration (int): Default duration for images if not provided in metadata.
    """
    try:
        # Load the main video
        main_clip = VideoFileClip(main_video_path)
        main_audio = main_clip.audio  # Extract the audio from the main video

        broll_overlays = []  # List to hold B-roll overlay clips
        overlay_times = []   # List to hold overlay times dynamically

        # Convert B-roll paths to VideoClips or ImageClips
        for broll in broll_paths:
            broll_path = Path("./media/images") / broll["broll_filename"]  # Properly join paths
            broll_path = broll_path.resolve()  # Get the absolute path

            if broll_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:  # Image file
                # Resize the image using Pillow
                with Image.open(broll_path) as img:
                    # Calculate the new size while maintaining the aspect ratio
                    new_width = 1024  # Example: Set a fixed width for resized images
                    aspect_ratio = img.height / img.width
                    new_height = int(new_width * aspect_ratio)

                    resized_image_path = broll_path.with_name(f"resized_{broll_path.name}")
                    img = img.resize((new_width, new_height), Image.ANTIALIAS)
                    img.save(resized_image_path)

                # Use the resized image for the ImageClip
                broll_clip = ImageClip(str(resized_image_path)).set_duration(broll.get("duration", image_duration))

            elif broll_path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:  # Video file
                broll_clip = VideoFileClip(str(broll_path)).without_audio()  # Remove audio from B-roll
                broll_clip = broll_clip.set_duration(broll.get("duration", broll_clip.duration))
            else:
                raise ValueError(f"Unsupported file format for B-roll: {broll_path}")

            # Position B-roll in the bottom-right corner
            broll_clip = broll_clip.set_position(("center"))

            broll_overlays.append(broll_clip)

            # Add timestamp from broll metadata
            overlay_times.append(broll["timestamp"])

        final_clips = [main_clip]

        # Overlay B-roll clips at the specified times
        for overlay, start_time in zip(broll_overlays, overlay_times):
            if start_time > main_clip.duration:
                break
            # Add the B-roll overlay to the main video
            overlay = overlay.set_start(start_time).set_end(start_time + overlay.duration)
            final_clips.append(overlay)

        # Create a composite video with all overlays
        composite_clip = CompositeVideoClip(final_clips).set_audio(main_audio)

        # Write the final output video
        composite_clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",  # Optional: faster encoding
                threads=4,           # Optional: multi-threading
                ffmpeg_params=["-vf", "scale=iw:-1"],  # Ensures correct scaling
            )
    except Exception as e:
        st.write(f"Error inserting B-roll: {e}")
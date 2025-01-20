import json
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx
from pathlib import Path


def add_zoom_effects_from_json(video_path, json_path, output_path):
    """
    Adds zoom effects to a video based on the configuration in a JSON file.

    Args:
        video_path (str): Path to the input video.
        json_path (str): Path to the JSON configuration file.
        output_path (str): Path to save the output video.
    """
    try:
        # Load the video
        video = VideoFileClip(video_path)
        clips = []
        start_time = 0  # Track the start time for non-zoom segments

        # Load zoom configuration from JSON
        with open(json_path, "r") as f:
            zoom_config = json.load(f)

        # Apply each zoom effect as specified in the JSON
        for zoom in zoom_config:
            from_ms = zoom.get("fromMs", 0)
            to_ms = zoom.get("toMs", 0)
            zoom_effect = zoom.get("zoomEffect", False)
            zoom_level = zoom.get("zoomLevel", 1.0)

            from_sec = from_ms / 1000  # Convert milliseconds to seconds
            to_sec = to_ms / 1000

            # Add the non-zoomed part before the zoom
            if start_time < from_sec:
                clips.append(video.subclip(start_time, from_sec))

            # Add the zoomed section
            if zoom_effect:
                zoom_clip = video.subclip(from_sec, to_sec).fx(vfx.resize, zoom_level)
                clips.append(zoom_clip)

            start_time = to_sec  # Update the start time

        # Add the remaining part of the video after the last zoom
        if start_time < video.duration:
            clips.append(video.subclip(start_time, video.duration))

        # Combine all clips
        final_clip = CompositeVideoClip(clips)

        # Write the output video
        final_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",  # Optional: faster encoding
                threads=4,           # Optional: multi-threading
                ffmpeg_params=["-vf", "scale=iw:-1"],  # Ensures correct scaling
            )
        print(f"Zoom effects applied and saved to {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add zoom effects to a video using a JSON configuration file.")
    parser.add_argument("input", help="Path to the input video")
    parser.add_argument("json", help="Path to the JSON configuration file")
    parser.add_argument("output", help="Path to the output video")

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    json_path = Path(args.json)
    if not input_path.exists():
        print(f"Input video not found: {args.input}")
        exit(1)
    if not json_path.exists():
        print(f"JSON configuration file not found: {args.json}")
        exit(1)

    # Run the zoom effects function
    add_zoom_effects_from_json(args.input, args.json, args.output)
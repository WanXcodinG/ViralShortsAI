import moviepy.editor as mp
from moviepy.editor import concatenate_videoclips
import json
import os
import streamlit as st
class SilenceTrimmer:
    def __init__(self, video_file, silence_file, output_path):
        self.video_file = video_file
        self.silence_file = silence_file
        self.output_path = output_path

    def load_silence_json(self):
        try:
            with open(self.silence_file, 'r') as f:
                st.write(f"Loading silence file: {self.silence_file}")
                return json.load(f)
        except Exception as e:
            st.warning(f"Error loading silence file: {e}")
            return []

    def calculate_non_silent_segments(self, silence_periods, video_duration):
        segments = []
        last_end = 0

        for silence in silence_periods:
            if silence["fromMs"] == 0:
                last_end = silence["toMs"]
                print(f"Skipping initial silent period: {silence}")
                continue

            if silence["fromMs"] > last_end:
                start_time = last_end / 1000
                end_time = silence["fromMs"] / 1000
                if start_time < end_time:  # Ensure valid segment
                    segments.append({
                        "start": start_time,
                        "end": end_time
                    })
                    print(f"Adding non-silent segment: start={start_time}, end={end_time}")
            last_end = silence["toMs"]

        if last_end < video_duration * 1000:
            start_time = last_end / 1000
            end_time = video_duration
            if start_time < end_time:  # Ensure valid segment
                segments.append({
                    "start": start_time,
                    "end": end_time
                })
                print(f"Adding final non-silent segment: start={start_time}, end={end_time}")

        print(f"Calculated non-silent segments: {segments}")
        return segments
    def trim_video(self):
        try:
            # Load video
            video = mp.VideoFileClip(str(self.video_file))

            # Load silence periods
            silence_periods = self.load_silence_json()
            if not silence_periods or len(silence_periods) == 0:
                st.warning("No silence periods found. Check your silence JSON file.")
                raise ValueError("No silence periods found. Check your silence JSON file.")

            # Calculate non-silent segments
            non_silent_segments = self.calculate_non_silent_segments(silence_periods, video.duration)
            st.write(f"Non-silent segments: {non_silent_segments}")

            # Filter out extremely short segments
            non_silent_segments = [
                seg for seg in non_silent_segments if (seg["end"] - seg["start"]) > 0.1
            ]
            if not non_silent_segments:
                st.write("No valid non-silent segments found.")
                raise ValueError("No valid non-silent segments found.")

            # Extract and concatenate non-silent segments
            clips = [
                video.subclip(seg["start"], min(seg["end"], video.duration)).resize(height=1920)
                for seg in non_silent_segments
            ]
            if not clips:
                st.write("No valid clips to concatenate. Check the calculated segments.")
                raise ValueError("No valid clips to concatenate. Check the calculated segments.")

            # Concatenate the clips
            trimmed_video = concatenate_videoclips(clips, method="compose")

            # Write the output video
            trimmed_video.write_videofile(
                self.output_path,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",  # Optional: faster encoding
                threads=4,           # Optional: multi-threading
                ffmpeg_params=["-vf", "scale=iw:-1"],  # Ensures correct scaling
            )
            st.write(f"Trimmed video saved to {self.output_path}")

        except Exception as e:
            st.write(f"Error trimming video: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure resources are released
            video.close()
            if 'trimmed_video' in locals():
                trimmed_video.close()
# Example Usage
if __name__ == "__main__":
    video_file = "./public/pawesome-closing.mp4"
    silence_file = "./public/silence.json"
    output_path = "./public/pawesome-closing-trimmed.mp4"

    trimmer = SilenceTrimmer(video_file, silence_file, output_path)
    trimmer.trim_video()
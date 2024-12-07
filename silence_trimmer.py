import moviepy.editor as mp
from moviepy.editor import concatenate_videoclips
import json
import os

class SilenceTrimmer:
    def __init__(self, video_file, silence_file, output_path):
        self.video_file = video_file
        self.silence_file = silence_file
        self.output_path = output_path

    def load_silence_json(self):
        try:
            with open(self.silence_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading silence file: {e}")
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
                segments.append({
                    "start": last_end / 1000,
                    "end": silence["fromMs"] / 1000
                })
                print(f"Adding non-silent segment: start={last_end}, end={silence['fromMs']}")
            last_end = silence["toMs"]

        if last_end < video_duration * 1000:
            segments.append({
                "start": last_end / 1000,
                "end": video_duration
            })
            print(f"Adding final non-silent segment: start={last_end}, end={video_duration * 1000}")

        print(f"Calculated non-silent segments: {segments}")
        return segments

    def trim_video(self):
        try:
            # Load video
            video = mp.VideoFileClip(self.video_file)

            # Load silence.json
            silence_periods = self.load_silence_json()

            # Calculate non-silent segments
            non_silent_segments = self.calculate_non_silent_segments(
                silence_periods, video.duration
            )

            # Extract and concatenate non-silent segments
            clips = [video.subclip(seg["start"], seg["end"]) for seg in non_silent_segments]
            trimmed_video = concatenate_videoclips(clips, method="compose")

            # Write the output video
            trimmed_video.write_videofile(self.output_path, codec="libx264", audio_codec="aac")
            print(f"Trimmed video saved to {self.output_path}")

        except Exception as e:
            print(f"Error trimming video: {e}")

        finally:
            video.close()

# Example Usage
if __name__ == "__main__":
    video_file = "./public/pawesome-closing.mp4"
    silence_file = "./public/silence.json"
    output_path = "./public/pawesome-closing-trimmed.mp4"

    trimmer = SilenceTrimmer(video_file, silence_file, output_path)
    trimmer.trim_video()
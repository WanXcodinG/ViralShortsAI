# silence_detector.py
import json
from pathlib import Path
import streamlit as st
def detect_silence(
    transcript_file: Path,
    silence_file: Path,
    silence_threshold: int = 2000,   # 2000ms
    confidence_threshold: float = 0.2
):
    """
    Detects silence periods in a transcript and writes them to a JSON file.
    
    Parameters:
        transcript_file (Path): Path to the transcript JSON file.
        silence_file (Path): Path to the output JSON file for silence periods.
        silence_threshold (int): Minimum gap (in ms) considered silence.
        confidence_threshold (float): Minimum confidence required to consider a word.
    """
    try:
        # Load transcript
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = json.load(f)

        # Filter out words below the confidence threshold
        filtered_transcript = [w for w in transcript if w.get("confidence", 0) >= confidence_threshold]

        # Sort the transcript by timestamp
        filtered_transcript.sort(key=lambda w: w.get("timestampMs", 0))

        silence_periods = []
        prev_end_ms = 0

        # Add silence before the first word if it starts after 0ms
        if filtered_transcript and filtered_transcript[0].get("timestampMs", 0) > 0:
            silence_periods.append({
                "fromMs": 0,
                "toMs": filtered_transcript[0]["timestampMs"]
            })
            prev_end_ms = filtered_transcript[0]["timestampMs"]

        # Detect silent periods between words using timestampMs
        for i in range(1, len(filtered_transcript)):
            current = filtered_transcript[i]
            gap = current["timestampMs"] - prev_end_ms

            if gap > silence_threshold:
                silence_periods.append({
                    "fromMs": prev_end_ms,
                    "toMs": current["timestampMs"]
                })

            prev_end_ms = current["timestampMs"]

        # Optionally, if the total video duration is known, add trailing silence
        # Example:
        # video_duration_ms = 60000  # 60 seconds example
        # if prev_end_ms < video_duration_ms:
        #     silence_periods.append({"fromMs": prev_end_ms, "toMs": video_duration_ms})

        # Write silence periods to the output file
        with open(silence_file, 'w', encoding='utf-8') as f:
            json.dump(silence_periods, f, indent=2)

        st.write(f"Silence periods saved to {silence_file}")

    except Exception as e:
        st.write(f"Error processing silence periods: {e}")


if __name__ == "__main__":
    # Example usage
    transcript_path = Path("./public/pawesome-closing.json")
    silence_path = Path("./public/silence.json")
    detect_silence(transcript_path, silence_path)
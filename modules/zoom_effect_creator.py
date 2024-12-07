from openai import OpenAI
from typing import List, Optional
from dotenv import load_dotenv 
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import List
from modules.structured_output import generate_structured_output
import streamlit as st
import json


load_dotenv()

class ZoomEffect(BaseModel):
    timestampMs: int
    zoomEffect: bool
    zoomLevel: float

class ZoomEffects(BaseModel):
    effects: List[ZoomEffect]

 
def create_zoom_effects(transcript_path: str, output_path: str):
    transcript_data = open(transcript_path, "r").read()

    prompt = (
        "You are an AI tool designed to optimize zoom effects for a viral TikTok video. "
        "You will receive a transcript in JSON format containing timestamps and dialogue from the video. "
        "Analyze the transcript to identify key moments that would benefit from zoom effects to enhance viewer engagement and highlight important actions or emotions. "
        "For each identified moment, specify the following in your response:"
        "\n- `timestampMs`: The start time in milliseconds when the zoom occurs."
        "\n- `zoomEffect`: A boolean indicating whether a zoom effect should be applied."
        "\n- `zoomLevel`: A float representing the intensity of the zoom (e.g., 1.0 for no zoom, 1.1 to 2 for different zoom levels)."
        "\n\nReturn your findings as a JSON array with objects in the following format:"
        "\n["
        "\n  {"
        "\n    \"fromMs\": 1000,"
        "\n    \"toMs\": 2000,"
        "\n    \"zoomEffect\": true,"
        "\n    \"zoomLevel\": 1.5"
        "\n  },"
        "\n  {"
        "\n    \"fromMs\": 3000,"
        "\n    \"toMs\": 4000,"
        "\n    \"zoomEffect\": false,"
        "\n    \"zoomLevel\": 1.0"
        "\n  }"
        "\n]"
        "\n\nHere is the input transcript:"
        f"\n{json.dumps(transcript_data, indent=2)}"
    )
    # Use the helper function
    try:
        zoom_effects = generate_structured_output(prompt, ZoomEffects)
        if zoom_effects:
            json.dump(zoom_effects.dict(), open(output_path, "w"), indent=2)
        else:
            st.write("Failed to generate structured output.")
    except ValidationError as e:
        st.write(f"Validation error: {e}")
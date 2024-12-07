# broll_suggester.py
# Suggests B-roll based on analyzed media and the marketing context using a structured output approach.

import json
from pydantic import BaseModel, RootModel
from typing import List
import openai
from modules.structured_output import generate_structured_output


class BrollOverlay(BaseModel):
    broll_filename: str  # The filename or path of the B-roll clip or image
    timestamp: float     # The time in the main video (in seconds) where the B-roll starts
    duration: float 

class BrollSuggestion(BaseModel):
    filename: str
    suggested_broll: List[BrollOverlay]  # Each dict contains B-roll filename, timestamp, and duration


class BrollSuggestions(BaseModel):
    suggestions: List[BrollSuggestion]


def suggest_broll(analyzed_media, marketing_context: str):
    # Convert analyzed_media to a JSON-friendly format (list of dicts)
    media_list = [m.dict() for m in analyzed_media]

    prompt = f"""
    You have a marketing context:
    {marketing_context}

    You have analyzed media items:
    {json.dumps(media_list, indent=2)}

    Based on these items, suggest suitable B-roll files to enhance the final video.
    For each analyzed media file, suggest the following:
    - B-roll files to use.
    - The timestamp (in seconds) where the B-roll should be overlaid.
    - The duration (in seconds) of the B-roll overlay.

    Return a JSON array of objects. Each object should have:
    - filename: The filename of a media file that needs B-roll.
    - suggested_broll: A list of objects, each with:
        - broll_filename: The filename or path of the B-roll clip or image.
        - timestamp: The time in the main video (in seconds) where the B-roll starts.
        - duration: The duration of the B-roll overlay (in seconds).

    Example JSON structure:
    [
      {{
        "filename": "video1.mp4",
        "suggested_broll": [
          {{
            "broll_filename": "broll_image1.png",
            "timestamp": 10,
            "duration": 5
          }},
          {{
            "broll_filename": "broll_clip2.mp4",
            "timestamp": 25,
            "duration": 8
          }}
        ]
      }}
    ]

    Return only valid JSON that matches the BrollSuggestions schema.
    """

    # Use the structured output helper with the BrollSuggestions model
    # to ensure the output adheres to the schema.
    suggestions = generate_structured_output(prompt, BrollSuggestions, [])
    if suggestions is None:
        # If parsing fails, return an empty list
        return []
    else:
        # Return the Python list from the BrollSuggestions model
        return suggestions.dict()["suggestions"]
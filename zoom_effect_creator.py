from openai import OpenAI
from typing import List, Optional
from dotenv import load_dotenv 
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import List
import os
import json


load_dotenv()

class ZoomEffect(BaseModel):
    timestampMs: int
    zoomEffect: bool
    zoomLevel: float

class ZoomEffects(BaseModel):
    effects: List[ZoomEffect]

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")
)

# Helper function for generating structured output
def generate_structured_output(prompt: str, model_class: BaseModel):
    try:
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "JSON: "},
            ],
            response_format=model_class,
        )
        structured_output = completion.choices[0].message
        parsed_content = json.loads(structured_output.content)
        return model_class(**parsed_content)
    except (ValidationError, json.JSONDecodeError) as ve:
        print(f"Validation or JSON decoding error in generate_structured_output: {ve}")
        return None
    except Exception as e:
        print(f"Error in generate_structured_output: {e}")
        if hasattr(e, 'response'):
            print("Raw API response:", e.response)
        return None
transcript_data = open("./public/pawesome-closing-trimmed.json", "r").read()

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
        json.dump(zoom_effects.dict(), open("./public/zoom_effects.json", "w"), indent=2)
    else:
        print("Failed to generate structured output.")
except ValidationError as e:
    print(f"Validation error: {e}")
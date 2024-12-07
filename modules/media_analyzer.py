# media_analyzer.py
import mimetypes
import json
import os
import base64
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageOps
from io import BytesIO
import cv2
from pathlib import Path

from modules.structured_output import generate_structured_output

load_dotenv()

client = OpenAI(
    organization=os.getenv("OPENAI_ORGANIZATION", "org-1JCjSS2HKnLP7MfrR5xZTElq"), 
    api_key=os.getenv("OPENAI_API_KEY")
)

class MediaItem(BaseModel):
    filename: str
    media_type: str  # "image", "video", etc.
    description: str
    relevance: str

def encode_image(image, max_size=(1024, 1024)):
    """
    Downscale and encode the image to Base64.
    """
    # Correct orientation using EXIF metadata
    image = ImageOps.exif_transpose(image)

    # Convert the image to RGB if it's in a mode like RGBA
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGB")

    # Downscale
    image.thumbnail(max_size, Image.ANTIALIAS)

    # Encode to base64 JPEG
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    img_byte = buffer.getvalue()
    return base64.b64encode(img_byte).decode('utf-8')

def extract_frame(video_path):
    """
    Extract a representative frame from the video as a PIL Image.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"Cannot open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        raise ValueError("No frames found in the video.")

    middle_frame_idx = total_frames // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise IOError("Failed to read frame from the video.")

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    return pil_image

def load_transcript_for_video(video_file: Path, transcript_dir: Path) -> str:
    """
    Load the transcript for the given video file if it exists.
    """
    transcript_file = transcript_dir / f"{video_file.stem}.json"
    if not transcript_file.exists():
        return ""
    try:
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        transcript_text = " ".join([seg["text"] for seg in transcript_data if "text" in seg])
        return transcript_text.strip()
    except Exception as e:
        print(f"Failed to load or parse transcript for {video_file}: {e}")
        return ""

def analyze_media_files(
    media_files,
    marketing_context: str,
    transcript_dir: Path = Path("./transcripts"),
    cache_path: Path = Path("./media_cache.json")
) -> List[MediaItem]:
    # Check if cache exists
    if cache_path.exists():
        # Load cached results
        with open(cache_path, 'r') as f:
            cached_data = json.load(f)
        # Convert cached dicts to MediaItem objects
        cached_items = [MediaItem(**item) for item in cached_data]
        return cached_items

    analyzed = []
    for f in media_files:
        f = Path(f)
        mtype, _ = mimetypes.guess_type(f)
        if mtype is None:
            media_type = "unknown"
        elif "image" in mtype:
            media_type = "image"
        elif "video" in mtype:
            media_type = "video"
        else:
            media_type = "other"

        image_data = None
        transcript_text = ""
        if media_type == "image":
            with Image.open(f) as img:
                image_data = encode_image(img)
        elif media_type == "video":
            try:
                frame_img = extract_frame(f)
                image_data = encode_image(frame_img)
                transcript_text = load_transcript_for_video(f, transcript_dir)
            except Exception as e:
                print(f"Frame extraction or transcript loading failed for {f}: {e}")
                image_data = None

        # Prepare messages for structured output
        # Remember: messages content must be a single string for each message.
        # Convert all previously used structures into plain strings.
        content_lines = []
        content_lines.append(f"Marketing Context: {marketing_context}")
        content_lines.append(f"File: {f.name}, Type: {media_type}")
        if transcript_text:
            content_lines.append(f"Transcript: {transcript_text}")
        if image_data:
            content_lines.append(f"Image: data:image/jpeg;base64,{image_data}")
            content_lines.append("Analyze this media (and transcript if present) and return valid JSON.")
        else:
            content_lines.append("No image available. Describe based on filename, marketing context, and transcript.")

        user_message = "\n".join(content_lines)

        # Create messages array as required by OpenAI API
        # The prompt is the system message
        system_prompt = (
            "You are analyzing a media file in the context of a marketing project. "
            "You will return a JSON describing filename, media_type, description, and relevance "
            "based on the marketing context, visual content, and (if available) the transcript text. "
            "The JSON structure should be:\n"
            "{\n"
            '  "filename": "string",\n'
            '  "media_type": "string",\n'
            '  "description": "string",\n'
            '  "relevance": "string"\n'
            "}\n"
            "No extra text, only return valid JSON."
        )

        messages = [
            {"role": "user", "content": user_message},
        ]

        # Call structured output function
        item = generate_structured_output(system_prompt, MediaItem, messages)
        if item is None:
            # Fallback item if parsing fails
            item = MediaItem(
                filename=f.name,
                media_type=media_type,
                description="No description found",
                relevance="unknown"
            )

        analyzed.append(item)

    # Save results to cache
    with open(cache_path, 'w') as f:
        json.dump([item.dict() for item in analyzed], f, indent=2)

    return analyzed
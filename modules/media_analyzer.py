# media_analyzer.py
import mimetypes
import json
import os
import base64
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from PIL import Image, ImageOps
from io import BytesIO
import cv2
from pathlib import Path
import datetime
import hashlib


class MediaItem(BaseModel):
    file_path: Path
    file_type: str  # "image", "video", etc.
    duration: Optional[float] = None  # for videos
    dimensions: Optional[tuple] = None  # (width, height)
    description: str
    suggested_usage: str
    tags: List[str] = []
    file_hash: str = ""
    analyzed_at: str = ""

def encode_image(image, max_size=(1024, 1024)):
    """
    Downscale and encode the image to Base64.
    """
    try:
        # Correct orientation using EXIF metadata
        image = ImageOps.exif_transpose(image)

        # Convert the image to RGB if it's in a mode like RGBA
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            image = image.convert("RGB")

        # Downscale
        image.thumbnail(max_size, Image.LANCZOS)

        # Encode to base64 JPEG
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        img_byte = buffer.getvalue()
        return base64.b64encode(img_byte).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def extract_frame(video_path, position=0.5):
    """
    Extract a representative frame from the video as a PIL Image.
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            raise ValueError("No frames found in the video.")

        frame_idx = int(total_frames * position)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise IOError("Failed to read frame from the video.")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        return pil_image
    except Exception as e:
        print(f"Error extracting frame from video {video_path}: {e}")
        return None

def get_video_info(video_path: Path) -> Dict[str, Any]:
    """
    Extract detailed information about a video file.
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {}
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration,
            "aspect_ratio": f"{width}:{height}"
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {}

def get_image_info(image_path: Path) -> Dict[str, Any]:
    """
    Extract detailed information about an image file.
    """
    try:
        with Image.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "format": img.format,
                "aspect_ratio": f"{img.width}:{img.height}"
            }
    except Exception as e:
        print(f"Error getting image info: {e}")
        return {}

def analyze_brightness(image: Image.Image) -> str:
    """
    Analyze the brightness of an image.
    """
    try:
        grayscale = image.convert('L')
        histogram = grayscale.histogram()
        pixels = sum(histogram)
        brightness = sum(i * histogram[i] for i in range(256)) / pixels
        
        if brightness < 85:
            return "dark"
        elif brightness > 170:
            return "bright"
        else:
            return "balanced"
    except:
        return "unknown"

def get_file_hash(filepath: Path) -> str:
    """
    Calculate a hash of the file content to identify changes.
    """
    try:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating file hash: {e}")
        return ""

def analyze_single_media_file(file_path: Path, context: str = "") -> MediaItem:
    """
    Analyze a single media file without AI.
    """
    # Determine media type
    mtype, _ = mimetypes.guess_type(file_path)
    if mtype is None:
        if file_path.suffix.lower() in [".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"]:
            file_type = "video"
        elif file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            file_type = "image"
        else:
            file_type = "unknown"
    elif "image" in mtype:
        file_type = "image"
    elif "video" in mtype:
        file_type = "video"
    else:
        file_type = "other"
    
    # Initialize variables
    duration = None
    dimensions = None
    tags = []
    description = ""
    suggested_usage = ""
    
    # Analyze based on file type
    if file_type == "image":
        info = get_image_info(file_path)
        if info:
            dimensions = (info.get("width"), info.get("height"))
            
            # Analyze image properties
            try:
                with Image.open(file_path) as img:
                    brightness = analyze_brightness(img)
                    tags.append(f"brightness:{brightness}")
                    
                    # Determine orientation
                    if dimensions[0] > dimensions[1]:
                        tags.append("landscape")
                        suggested_usage = "Good for wide shots, backgrounds, or establishing scenes"
                    elif dimensions[0] < dimensions[1]:
                        tags.append("portrait")
                        suggested_usage = "Perfect for mobile-first content, close-ups, or single subjects"
                    else:
                        tags.append("square")
                        suggested_usage = "Ideal for social media posts or balanced compositions"
                    
                    # Basic description
                    description = f"{file_path.name}: {dimensions[0]}x{dimensions[1]} {file_type}, {brightness} lighting"
            except:
                description = f"{file_path.name}: Image file"
                suggested_usage = "Could be used for various purposes"
    
    elif file_type == "video":
        info = get_video_info(file_path)
        if info:
            duration = info.get("duration", 0)
            dimensions = (info.get("width"), info.get("height"))
            fps = info.get("fps", 0)
            
            # Analyze video properties
            if duration < 5:
                tags.append("short-clip")
                suggested_usage = "Quick transition, intro/outro, or accent clip"
            elif duration < 15:
                tags.append("medium-clip")
                suggested_usage = "Main content segment, key message delivery"
            else:
                tags.append("long-clip")
                suggested_usage = "Extended content, can be cut into multiple segments"
            
            # Check aspect ratio
            if dimensions[0] > dimensions[1]:
                tags.append("landscape")
            elif dimensions[0] < dimensions[1]:
                tags.append("portrait")
                tags.append("mobile-optimized")
            
            # FPS tags
            if fps >= 60:
                tags.append("high-fps")
                tags.append("smooth-motion")
            elif fps >= 24:
                tags.append("standard-fps")
            
            description = f"{file_path.name}: {dimensions[0]}x{dimensions[1]} video, {round(duration, 2)}s at {round(fps)}fps"
        else:
            description = f"{file_path.name}: Video file"
            suggested_usage = "Video content"
    
    else:
        description = f"{file_path.name}: {file_type} file"
        suggested_usage = "File type not fully supported"
    
    # Add context-based tags if provided
    if context:
        context_lower = context.lower()
        if any(word in context_lower for word in ["product", "demo", "showcase"]):
            tags.append("product-focused")
        if any(word in context_lower for word in ["tutorial", "how-to", "guide"]):
            tags.append("educational")
        if any(word in context_lower for word in ["promo", "sale", "discount"]):
            tags.append("promotional")
    
    return MediaItem(
        file_path=file_path,
        file_type=file_type,
        duration=duration,
        dimensions=dimensions,
        description=description,
        suggested_usage=suggested_usage,
        tags=tags,
        file_hash=get_file_hash(file_path),
        analyzed_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def analyze_media_files(
    media_files: List[Path],
    context: str = "",
    cache_path: Path = None
) -> List[MediaItem]:
    """
    Analyze multiple media files.
    """
    # Load cache if available
    cached_items = []
    cached_file_dict = {}
    if cache_path and cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            for item_data in cached_data:
                item_data['file_path'] = Path(item_data['file_path'])
                cached_items.append(MediaItem(**item_data))
            cached_file_dict = {item.file_path.name: (item, item.file_hash) for item in cached_items}
        except Exception as e:
            print(f"Error loading cache: {e}")
    
    # Analyze files
    all_items = []
    processed_files = set()
    
    for file_path in media_files:
        try:
            file_path = Path(file_path).resolve()
            file_hash = get_file_hash(file_path)
            processed_files.add(file_path.name)
            
            # Use cache if file hasn't changed
            if file_path.name in cached_file_dict and cached_file_dict[file_path.name][1] == file_hash:
                all_items.append(cached_file_dict[file_path.name][0])
                continue
            
            # Analyze the file
            item = analyze_single_media_file(file_path, context)
            all_items.append(item)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            continue
    
    # Include cached items that weren't in the current media_files
    for cached_item in cached_items:
        if cached_item.file_path.name not in processed_files:
            all_items.append(cached_item)
    
    # Save cache if path provided
    if cache_path:
        try:
            cache_data = []
            for item in all_items:
                item_dict = item.dict()
                item_dict['file_path'] = str(item_dict['file_path'])
                cache_data.append(item_dict)
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    return all_items
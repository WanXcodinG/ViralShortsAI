# broll_suggester.py
# Suggests B-roll based on analyzed media and context using intelligent rule-based algorithms

import json
import random
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path

class BrollScene(BaseModel):
    scene_number: int
    description: str
    duration: float
    media_files: List[str]  # List of media file paths
    transition: str  # Type of transition (cut, fade, dissolve, etc.)

def calculate_scene_pacing(total_duration: float, style: str = "dynamic") -> List[float]:
    """
    Calculate scene durations based on pacing style.
    """
    if style == "dynamic":
        # Fast-paced, many quick cuts
        min_duration = 1.5
        max_duration = 4.0
    elif style == "calm":
        # Slower pacing, longer scenes
        min_duration = 3.0
        max_duration = 8.0
    elif style == "energetic":
        # Very fast cuts
        min_duration = 0.8
        max_duration = 3.0
    else:  # emotional or standard
        min_duration = 2.0
        max_duration = 6.0
    
    scenes = []
    current_time = 0.0
    
    while current_time < total_duration:
        # Use random duration within range, with variation
        duration = random.uniform(min_duration, max_duration)
        
        # Ensure we don't exceed total duration
        if current_time + duration > total_duration:
            duration = total_duration - current_time
        
        if duration > 0.5:  # Only add scenes longer than 0.5 seconds
            scenes.append(duration)
        current_time += duration
    
    return scenes

def select_media_for_scene(
    analyzed_media,
    scene_type: str,
    scene_duration: float,
    used_media: set
) -> List[str]:
    """
    Select appropriate media files for a scene based on type and requirements.
    """
    selected = []
    
    # Filter out already used media for variety
    available_media = [m for m in analyzed_media if str(m.file_path) not in used_media]
    if not available_media:
        available_media = analyzed_media  # Reset if we've used everything
    
    # Scene type specific selection
    if scene_type == "intro":
        # Prefer establishing shots, landscapes, or branded content
        candidates = [m for m in available_media if 
                     any(tag in m.tags for tag in ["landscape", "establishing", "product-focused"])]
        if not candidates:
            candidates = available_media
    
    elif scene_type == "action":
        # Prefer dynamic content, short clips
        candidates = [m for m in available_media if 
                     any(tag in m.tags for tag in ["short-clip", "high-fps", "energetic"])]
        if not candidates:
            candidates = [m for m in available_media if m.file_type == "video"]
    
    elif scene_type == "detail":
        # Prefer close-ups, product shots, portrait orientation
        candidates = [m for m in available_media if 
                     any(tag in m.tags for tag in ["portrait", "product-focused", "detail"])]
        if not candidates:
            candidates = available_media
    
    elif scene_type == "transition":
        # Prefer images or very short clips
        candidates = [m for m in available_media if 
                     m.file_type == "image" or "short-clip" in m.tags]
        if not candidates:
            candidates = available_media
    
    else:  # general
        candidates = available_media
    
    # Select based on duration requirements
    if scene_duration < 2.0:
        # For very short scenes, prefer images or short clips
        final_candidates = [m for m in candidates if 
                           m.file_type == "image" or 
                           (m.duration and m.duration <= scene_duration * 2)]
    else:
        # For longer scenes, prefer videos with sufficient duration
        final_candidates = [m for m in candidates if 
                           m.file_type == "video" and 
                           m.duration and m.duration >= scene_duration * 0.7]
    
    if not final_candidates:
        final_candidates = candidates
    
    # Select the best candidate
    if final_candidates:
        selected_media = random.choice(final_candidates)
        selected.append(str(selected_media.file_path))
        used_media.add(str(selected_media.file_path))
    
    return selected

def determine_scene_types(num_scenes: int, context: str) -> List[str]:
    """
    Determine scene types based on number of scenes and context.
    """
    scene_types = []
    
    # Always start with intro and end with outro
    if num_scenes == 1:
        return ["general"]
    elif num_scenes == 2:
        return ["intro", "outro"]
    
    # Analyze context for scene type hints
    context_lower = context.lower()
    is_product = any(word in context_lower for word in ["product", "demo", "showcase"])
    is_tutorial = any(word in context_lower for word in ["tutorial", "how-to", "guide"])
    is_promo = any(word in context_lower for word in ["promo", "sale", "discount"])
    
    # Build scene sequence
    scene_types.append("intro")
    
    middle_scenes = num_scenes - 2  # Excluding intro and outro
    
    if is_product:
        # Product videos: intro -> detail -> action -> detail -> outro
        pattern = ["detail", "action"]
    elif is_tutorial:
        # Tutorial videos: intro -> general -> detail -> general -> outro
        pattern = ["general", "detail"]
    elif is_promo:
        # Promo videos: intro -> action -> transition -> action -> outro
        pattern = ["action", "transition"]
    else:
        # Default pattern
        pattern = ["general", "action", "detail"]
    
    # Fill middle scenes
    for i in range(middle_scenes):
        scene_types.append(pattern[i % len(pattern)])
    
    scene_types.append("outro")
    
    return scene_types

def select_transition(scene_index: int, total_scenes: int, style: str) -> str:
    """
    Select appropriate transition based on position and style.
    """
    if scene_index == 0:
        return "fade_in"
    elif scene_index == total_scenes - 1:
        return "fade_out"
    
    if style == "dynamic":
        transitions = ["cut", "cut", "cut", "swipe", "zoom"]
    elif style == "calm":
        transitions = ["fade", "dissolve", "fade", "crossfade"]
    elif style == "energetic":
        transitions = ["cut", "cut", "whip", "zoom", "glitch"]
    else:
        transitions = ["cut", "fade", "dissolve"]
    
    return random.choice(transitions)

def suggest_broll(
    analyzed_media,
    context: str,
    target_duration: float = 30.0,
    style: str = "dynamic"
) -> List[Dict[str, Any]]:
    """
    Suggests B-roll scenes based on analyzed media and context.
    
    Args:
        analyzed_media: List of MediaItem objects from media analysis
        context: Marketing or creative context for the video
        target_duration: Target video duration in seconds
        style: Video style (dynamic, calm, energetic, emotional)
    
    Returns:
        List of B-roll scene suggestions
    """
    if not analyzed_media:
        return []
    
    # Calculate scene durations
    scene_durations = calculate_scene_pacing(target_duration, style)
    num_scenes = len(scene_durations)
    
    # Determine scene types
    scene_types = determine_scene_types(num_scenes, context)
    
    # Track used media for variety
    used_media = set()
    
    # Generate B-roll scenes
    broll_scenes = []
    
    for i, (duration, scene_type) in enumerate(zip(scene_durations, scene_types)):
        # Select media for this scene
        media_files = select_media_for_scene(
            analyzed_media,
            scene_type,
            duration,
            used_media
        )
        
        # Create scene description
        descriptions = {
            "intro": "Opening scene to establish context and grab attention",
            "outro": "Closing scene with call-to-action or branding",
            "action": "Dynamic scene showing product/service in action",
            "detail": "Close-up or detail shot highlighting key features",
            "transition": "Brief transitional moment between main scenes",
            "general": "Supporting content that reinforces the main message"
        }
        
        description = descriptions.get(scene_type, "Content scene")
        
        # Select transition
        transition = select_transition(i, num_scenes, style)
        
        # Create scene object
        scene = {
            "scene_number": i + 1,
            "description": description,
            "duration": round(duration, 1),
            "media_files": media_files,
            "transition": transition,
            "scene_type": scene_type  # Additional metadata
        }
        
        broll_scenes.append(scene)
    
    # Add metadata about the suggestion
    result = {
        "target_duration": target_duration,
        "actual_duration": sum(scene["duration"] for scene in broll_scenes),
        "style": style,
        "total_scenes": len(broll_scenes),
        "scenes": broll_scenes,
        "context_summary": context[:200] + "..." if len(context) > 200 else context
    }
    
    return broll_scenes  # Return just the scenes list for compatibility 
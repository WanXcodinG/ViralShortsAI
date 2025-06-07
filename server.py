#!/usr/bin/env python3
"""
ViralShortAI MCP Server

A FastMCP server that provides tools for creating viral short-form videos
from a directory of media files (videos, photos) and context.
"""

from fastmcp import FastMCP
from pathlib import Path
import json
import shutil
import subprocess
import os
import time
import tempfile
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# Import existing modules
from modules.directory_reader import gather_media_files
from modules.media_analyzer import analyze_media_files
from modules.broll_suggester import suggest_broll
from modules.voiceover_generator import generate_voiceover
from modules.config import get_elevenlabs_api_key

# Create FastMCP server instance
mcp = FastMCP(
    "ViralShortAI",
    description="Create viral short-form videos for TikTok, YouTube Shorts, and Instagram Reels"
)

# Data models
class MediaAnalysis(BaseModel):
    file_path: str
    file_type: str
    duration: Optional[float]
    description: str
    suggested_usage: str
    tags: List[str]

class BrollSuggestion(BaseModel):
    scene_number: int
    description: str
    duration: float
    media_files: List[str]
    transition: str

class VideoProject(BaseModel):
    project_id: str
    media_directory: str
    context_path: Optional[str]
    output_directory: str
    created_at: datetime
    status: str

# Store active projects
active_projects: Dict[str, VideoProject] = {}

@mcp.tool()
def analyze_media_directory(directory_path: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze all media files in a directory and return detailed information about each file.
    
    Args:
        directory_path: Path to directory containing media files
        context: Optional marketing/creative context to inform analysis
    
    Returns:
        Analysis results including file details, descriptions, and usage suggestions
    """
    media_dir = Path(directory_path)
    if not media_dir.exists():
        return {"error": f"Directory not found: {directory_path}"}
    
    # Gather media files
    media_files = gather_media_files(media_dir)
    if not media_files:
        return {"error": "No media files found in directory", "directory": directory_path}
    
    # Analyze media files
    analyzed_media = analyze_media_files(media_files, context or "")
    
    # Convert to dictionary format
    results = {
        "directory": directory_path,
        "total_files": len(media_files),
        "media_analysis": []
    }
    
    for media in analyzed_media:
        analysis = {
            "file_path": str(media.file_path),
            "file_type": media.file_type,
            "duration": media.duration,
            "description": media.description,
            "suggested_usage": media.suggested_usage,
            "tags": media.tags
        }
        results["media_analysis"].append(analysis)
    
    return results

@mcp.tool()
def create_video_project(
    media_directory: str,
    output_directory: str,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new video project for generating short-form content.
    
    Args:
        media_directory: Path to directory containing source media files
        output_directory: Path where generated videos will be saved
        context: Optional marketing or creative context for the video
    
    Returns:
        Project details including project ID
    """
    project_id = f"project_{int(time.time())}"
    
    # Create output directory if it doesn't exist
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save context if provided
    context_path = None
    if context:
        context_dir = output_path / "context"
        context_dir.mkdir(exist_ok=True)
        context_path = context_dir / f"{project_id}_context.md"
        context_path.write_text(context)
    
    project = VideoProject(
        project_id=project_id,
        media_directory=media_directory,
        context_path=str(context_path) if context_path else None,
        output_directory=output_directory,
        created_at=datetime.now(),
        status="created"
    )
    
    active_projects[project_id] = project
    
    return {
        "project_id": project_id,
        "media_directory": media_directory,
        "output_directory": output_directory,
        "context_saved": bool(context_path),
        "status": "created"
    }

@mcp.tool()
def suggest_broll_scenes(
    project_id: str,
    video_duration: int = 30,
    style: str = "dynamic"
) -> Dict[str, Any]:
    """
    Suggest B-roll scenes based on analyzed media files and project context.
    
    Args:
        project_id: ID of the video project
        video_duration: Target video duration in seconds (default: 30)
        style: Video style - "dynamic", "calm", "energetic", "emotional"
    
    Returns:
        B-roll suggestions with scene descriptions and recommended media files
    """
    if project_id not in active_projects:
        return {"error": f"Project not found: {project_id}"}
    
    project = active_projects[project_id]
    media_dir = Path(project.media_directory)
    
    # Get context if available
    context = ""
    if project.context_path and Path(project.context_path).exists():
        context = Path(project.context_path).read_text()
    
    # Analyze media files
    media_files = gather_media_files(media_dir)
    if not media_files:
        return {"error": "No media files found in project"}
    
    analyzed_media = analyze_media_files(media_files, context)
    
    # Get B-roll suggestions
    suggestions = suggest_broll(analyzed_media, context)
    
    return {
        "project_id": project_id,
        "total_scenes": len(suggestions),
        "target_duration": video_duration,
        "style": style,
        "scenes": suggestions
    }

@mcp.tool()
def create_voiceover(
    project_id: str,
    voiceover_text: str,
    voice: str = "Rachel",
    model: str = "eleven_multilingual_v2"
) -> Dict[str, Any]:
    """
    Generate voiceover audio using ElevenLabs API.
    
    Args:
        project_id: ID of the video project
        voiceover_text: Text to convert to speech
        voice: ElevenLabs voice ID or name (default: "Rachel")
        model: ElevenLabs model to use
    
    Returns:
        Path to generated voiceover file and duration
    """
    if project_id not in active_projects:
        return {"error": f"Project not found: {project_id}"}
    
    project = active_projects[project_id]
    output_dir = Path(project.output_directory)
    
    # Generate unique filename
    voiceover_filename = f"{project_id}_voiceover_{int(time.time())}.mp3"
    voiceover_path = output_dir / voiceover_filename
    
    try:
        # Get API key
        api_key = get_elevenlabs_api_key()
        if not api_key:
            return {"error": "ElevenLabs API key not configured"}
        
        # Generate voiceover
        generate_voiceover(
            voiceover_text,
            str(voiceover_path),
            api_key,
            voice=voice,
            model=model
        )
        
        # Get duration (you might need to add a function to get audio duration)
        # For now, estimate based on text length
        estimated_duration = len(voiceover_text.split()) / 150 * 60  # 150 words per minute
        
        return {
            "project_id": project_id,
            "voiceover_path": str(voiceover_path),
            "voiceover_text": voiceover_text,
            "voice": voice,
            "estimated_duration": estimated_duration,
            "status": "generated"
        }
    except Exception as e:
        return {"error": f"Failed to generate voiceover: {str(e)}"}

@mcp.tool()
def generate_video(
    project_id: str,
    broll_scenes: List[Dict[str, Any]],
    voiceover_path: Optional[str] = None,
    video_style: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate the final video using specified B-roll scenes and optional voiceover.
    
    Args:
        project_id: ID of the video project
        broll_scenes: List of B-roll scene specifications
        voiceover_path: Optional path to voiceover audio file
        video_style: Optional styling parameters (transitions, effects, etc.)
    
    Returns:
        Path to generated video file and metadata
    """
    if project_id not in active_projects:
        return {"error": f"Project not found: {project_id}"}
    
    project = active_projects[project_id]
    media_dir = Path(project.media_directory)
    output_dir = Path(project.output_directory)
    
    try:
        # Import video processor when needed
        from modules.video_processor import process_videos
        
        # Process the video
        voiceover = Path(voiceover_path) if voiceover_path else None
        
        final_video_path = process_videos(
            media_dir,
            output_dir,
            broll_scenes,
            voiceover
        )
        
        # Generate unique output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{project_id}_viral_short_{timestamp}.mp4"
        final_output_path = output_dir / output_filename
        
        # Move to final location
        if final_video_path.exists():
            shutil.move(str(final_video_path), str(final_output_path))
        else:
            return {"error": "Video generation failed - output file not found"}
        
        # Update project status
        project.status = "completed"
        
        return {
            "project_id": project_id,
            "video_path": str(final_output_path),
            "video_filename": output_filename,
            "duration": 30,  # You might want to get actual duration
            "status": "completed",
            "created_at": timestamp
        }
    except Exception as e:
        return {"error": f"Failed to generate video: {str(e)}"}

@mcp.tool()
def list_projects() -> List[Dict[str, Any]]:
    """
    List all active video projects.
    
    Returns:
        List of project summaries
    """
    projects = []
    for project_id, project in active_projects.items():
        projects.append({
            "project_id": project_id,
            "media_directory": project.media_directory,
            "output_directory": project.output_directory,
            "created_at": project.created_at.isoformat(),
            "status": project.status,
            "has_context": bool(project.context_path)
        })
    return projects

@mcp.tool()
def get_project_details(project_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific project.
    
    Args:
        project_id: ID of the video project
    
    Returns:
        Detailed project information including media analysis
    """
    if project_id not in active_projects:
        return {"error": f"Project not found: {project_id}"}
    
    project = active_projects[project_id]
    
    # Get media analysis
    media_analysis = analyze_media_directory(
        project.media_directory,
        Path(project.context_path).read_text() if project.context_path else None
    )
    
    # List output files
    output_files = []
    output_dir = Path(project.output_directory)
    if output_dir.exists():
        for file in output_dir.glob(f"{project_id}_*.mp4"):
            output_files.append(str(file))
    
    return {
        "project_id": project_id,
        "media_directory": project.media_directory,
        "output_directory": project.output_directory,
        "created_at": project.created_at.isoformat(),
        "status": project.status,
        "context_path": project.context_path,
        "media_analysis": media_analysis,
        "output_files": output_files
    }

@mcp.tool()
def export_video_metadata(project_id: str, video_path: str) -> Dict[str, Any]:
    """
    Export metadata for a generated video (for social media posting).
    
    Args:
        project_id: ID of the video project
        video_path: Path to the generated video
    
    Returns:
        Metadata including suggested captions, hashtags, and posting times
    """
    if project_id not in active_projects:
        return {"error": f"Project not found: {project_id}"}
    
    project = active_projects[project_id]
    
    # Get context for metadata generation
    context = ""
    if project.context_path and Path(project.context_path).exists():
        context = Path(project.context_path).read_text()
    
    # Basic metadata (you could enhance this with actual analysis)
    metadata = {
        "project_id": project_id,
        "video_path": video_path,
        "platforms": {
            "tiktok": {
                "max_duration": 60,
                "recommended_duration": 30,
                "aspect_ratio": "9:16",
                "suggested_hashtags": ["#viral", "#fyp", "#trending"],
                "best_posting_times": ["6:00 AM", "10:00 AM", "7:00 PM", "10:00 PM"]
            },
            "youtube_shorts": {
                "max_duration": 60,
                "recommended_duration": 30,
                "aspect_ratio": "9:16",
                "suggested_hashtags": ["#shorts", "#viral", "#trending"],
                "best_posting_times": ["12:00 PM", "3:00 PM", "7:00 PM"]
            },
            "instagram_reels": {
                "max_duration": 90,
                "recommended_duration": 30,
                "aspect_ratio": "9:16",
                "suggested_hashtags": ["#reels", "#viral", "#explore"],
                "best_posting_times": ["11:00 AM", "2:00 PM", "5:00 PM", "8:00 PM"]
            }
        },
        "context": context[:200] + "..." if len(context) > 200 else context
    }
    
    return metadata

# Server startup
if __name__ == "__main__":
    mcp.run()

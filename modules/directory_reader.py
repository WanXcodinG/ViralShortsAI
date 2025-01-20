# This module scans the media directory and returns a list of files.
# Each file will later be analyzed by the media_analyzer module.

from pathlib import Path

def gather_media_files(media_dir: Path):
    """
    Gather all media files from the given directory, including images, videos, and JSON files.
    """
    # Define the extensions to include
    allowed_extensions = ['mp4', 'mov', 'jpg', 'jpeg', 'png']
    
    # Check if the directory exists
    if not media_dir.exists():
        return []
    
    # Gather files matching the allowed extensions (case-insensitive)
    media_files = [
        file for ext in allowed_extensions
        for file in media_dir.rglob(f'*.{ext}')
    ]
    
    return media_files
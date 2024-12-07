# This module scans the media directory and returns a list of files.
# Each file will later be analyzed by the media_analyzer module.

from pathlib import Path

def gather_media_files(media_dir: Path):
    # Return a list of all media files in the media directory
    # including images, videos, screen recordings, etc.
    if not media_dir.exists():
        return []
    return list(media_dir.glob('**/*.*'))  # Adjust pattern as needed
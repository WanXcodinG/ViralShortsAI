# ViralShortAI MCP Server

A FastMCP server that provides tools for creating viral short-form videos for TikTok, YouTube Shorts, and Instagram Reels. This server exposes video editing capabilities as tools that can be used by LLMs to automatically generate engaging content from a directory of media files.

## Features

- **Media Analysis**: Automatically analyze videos and images to understand content
- **Intelligent B-roll Suggestions**: Smart scene composition based on content type
- **Voiceover Generation**: Text-to-speech using ElevenLabs API
- **Video Processing**: Automated video editing with transitions and effects
- **Multi-Platform Optimization**: Export settings for TikTok, YouTube Shorts, and Instagram Reels

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/viralshortai.git
cd viralshortai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ElevenLabs API key
```

4. Run the MCP server:
```bash
python server.py
```

## Usage with Claude Desktop

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "viralshortai": {
      "command": "python",
      "args": ["/path/to/viralshortai/server.py"],
      "env": {
        "ELEVENLABS_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Available Tools

### 1. `analyze_media_directory`
Analyzes all media files in a directory and returns detailed information about each file.

**Example prompt**: "Analyze the media files in /Users/me/content/videos"

### 2. `create_video_project`
Creates a new video project for generating short-form content.

**Example prompt**: "Create a new video project using media from /Users/me/content with context about my product launch"

### 3. `suggest_broll_scenes`
Suggests B-roll scenes based on analyzed media files and project context.

**Example prompt**: "Suggest dynamic B-roll scenes for a 30-second video"

### 4. `create_voiceover`
Generates voiceover audio using ElevenLabs API.

**Example prompt**: "Create a voiceover saying 'Check out our amazing new product!'"

### 5. `generate_video`
Generates the final video using specified B-roll scenes and optional voiceover.

**Example prompt**: "Generate the final video with the suggested B-roll and voiceover"

### 6. `export_video_metadata`
Exports metadata for social media posting including hashtags and optimal posting times.

**Example prompt**: "Export metadata for posting the video on TikTok"

## Example Workflow

Here's a typical conversation with Claude to create a viral video:

```
User: I have a folder of product photos and videos at /Users/me/products. 
      Can you create a viral TikTok video showcasing our new smartwatch?

Claude: I'll help you create a viral TikTok video for your smartwatch. Let me start by 
        analyzing your media files and creating a video project.

[Claude uses analyze_media_directory, create_video_project, suggest_broll_scenes, 
 create_voiceover, and generate_video tools]

Claude: I've created a 30-second viral video for your smartwatch! The video includes:
        - Dynamic product shots with smooth transitions
        - An engaging voiceover highlighting key features
        - Optimized for TikTok's 9:16 aspect ratio
        
        The video has been saved to: /Users/me/products/output/project_1234_viral_short.mp4
```

## Media Directory Structure

For best results, organize your media files like this:

```
media_directory/
├── videos/
│   ├── product_demo.mp4
│   ├── unboxing.mp4
│   └── features.mp4
├── images/
│   ├── product_shot_1.jpg
│   ├── product_shot_2.jpg
│   └── lifestyle.jpg
└── context/
    └── marketing.txt (optional marketing context)
```

## Configuration

### ElevenLabs API Key

Set your ElevenLabs API key in the environment:

```bash
export ELEVENLABS_API_KEY="your-api-key-here"
```

Or add it to your `.env` file:

```
ELEVENLABS_API_KEY=your-api-key-here
```

### Video Styles

The server supports multiple video styles:
- **dynamic**: Fast-paced with quick cuts (1.5-4s per scene)
- **calm**: Slower pacing with longer scenes (3-8s per scene)
- **energetic**: Very fast cuts (0.8-3s per scene)
- **emotional**: Standard pacing (2-6s per scene)

## Troubleshooting

### No media files found
- Ensure your media files are in supported formats: MP4, MOV, JPG, PNG
- Check that the directory path is correct

### Voiceover generation fails
- Verify your ElevenLabs API key is valid
- The server will fall back to a free TTS service if ElevenLabs fails

### Video processing errors
- Ensure FFmpeg is installed on your system
- Check that you have sufficient disk space for video processing

## License

MIT License - see LICENSE file for details 
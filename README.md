# **ViralShortsAI**

**ViralShortsAI** is an end-to-end automated video generation pipeline designed to create engaging, TikTok-style viral short videos using AI. The project leverages LLMs and audio/video processing techniques to automate content creation for your marketing needs.

## New Agentic Features!

ViralShortsAI now includes powerful autonomous features:

- **One-Shot Video Generation**: Provide a marketing prompt, and the system will automatically generate a complete video
- **Continuous Content Generation**: Set up automatic video production on a schedule
- **Smart Media Analysis**: AI-powered analysis of your images and videos to select the best content
- **Contextual B-Roll**: Automatically selects and inserts B-roll clips that enhance your message
- **Dynamic Voiceovers**: Generates natural-sounding voiceovers from your marketing context
- **Fault Tolerance**: Robust error handling ensures the system keeps working even when components fail

## How It Works

1. **Add your media**: Place photos and videos in the `media` directory
2. **Set your context**: Update `context/marketing.md` with your marketing message
3. **Run the app**: Start the Streamlit app and provide a prompt
4. **Get results**: The system creates a polished video with captions, B-roll, and voiceover

## Key Features

**Media Analysis & Enhancement:**
- Automatically analyzes images and videos using AI
- Suggests appropriate B-roll and visual enhancements
- Generates voiceovers using ElevenLabs or fallback TTS services

**Intelligent Video Editing:**
- Detects and trims silence
- Applies dynamic zoom effects based on content
- Inserts B-roll at optimal moments
- Adds captions using Whisper and Remotion

**Autonomous Operation:**
- Continuous generation mode for ongoing content production
- Progress tracking and status reporting
- Comprehensive error handling and fallback options
- Production logging and history

## Setup Instructions

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ViralShortAI.git
cd ViralShortAI

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd js-scripts
npm install
cd ..
```

### 2. Configuration

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key
```

### 3. Directory Structure

Ensure you have the following directory structure for your media:

```
media/
├── videos/      # Place your main video files here
├── images/      # Images for B-roll
├── subs/        # Subtitle files (auto-generated)
├── audio/       # Audio clips (optional)
└── screen_recordings/ # Screen recordings (optional)
```

## Usage

### Starting the Application

```bash
streamlit run app.py
```

### One-Shot Video Creation

1. Enter your marketing prompt in the text area
2. Click "Generate Content Now"
3. The system will:
   - Update your marketing context based on your prompt
   - Analyze all media files
   - Generate B-roll suggestions
   - Create a voiceover
   - Process videos with captions and effects
   - Present the final video

### Continuous Generation

1. Enter your marketing prompt
2. Adjust the content generation interval (hours)
3. Click "Start Continuous Generation"
4. The system will automatically create new videos at the specified interval
5. View the "Recent Productions" section to see generated videos

### Viewing Results

The final videos are saved in the `js-scripts/public` directory and can be viewed directly in the Streamlit app or using any video player.

## Customization

### Marketing Context

Edit `context/marketing.md` to change the base marketing message. This file contains the foundational information about your product or service.

### Media Files

- Add your own videos to `media/videos/`
- Add images for B-roll to `media/images/`
- The system will automatically analyze and incorporate these files

## Troubleshooting

- **API Key Issues**: Ensure your API keys are correctly set in the `.env` file
- **Missing Media**: Make sure you have videos in the `media/videos/` directory
- **Node.js Errors**: Check that you have installed Node.js and the required dependencies
- **FFmpeg Issues**: Ensure FFmpeg is installed on your system for video processing

## Dependencies

### Python Packages:
- moviepy, opencv-python, pillow, streamlit, openai, pydantic, elevenlabs, etc.

### Node.js Packages:
- remotion and related packages for video rendering
- chokidar for file watching

### External Tools:
- FFmpeg for media processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

---

Happy video creation with ViralShortsAI! 🎬✨


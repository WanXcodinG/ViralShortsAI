# **ViralShortsAI**

## This is still a work in progress!

**ViralShortsAI** is an end-to-end automated video generation pipeline designed to create engaging, TikTok-style viral short videos using AI. The project leverages LLMs and audio/video processing techniques to:

- Analyze and enhance media assets using AI (via OpenAI and ElevenLabs).
- Suggest and overlay B-roll to enrich the final video.
- Generate voiceovers and captions using Whisper, Remotion, and Node.js.
- Trim silence and apply creative zoom effects for dynamic video editing.

This repository is ideal for creators and marketers who want to automate the production of eye-catching short videos with minimal manual intervention.

**Features**

**Green Screen Overlay:**

The ai_video.py script processes a video to detect a green screen area and overlays a separate screen recording with perspective correction.

**Media Analysis & B-Roll Suggestions:**

Using the media_analyzer.py and broll_suggester.py modules, the project analyzes media files and, in the context of a marketing message (see context/marketing.md), suggests appropriate B-roll clips to overlay onto the main video.

**Voiceover Generation:**

The voiceover_generator.py module uses the ElevenLabs API to convert marketing copy into a synthesized voiceover.

**Silence Detection & Trimming:**

The silence.py and silence_trimmer.py modules detect silent periods in video transcripts and trim the main video accordingly.

**Dynamic Zoom Effects:**

The project can apply creative zoom effects based on transcript analysis using zoom_effect_creator.py and zoomer.py.

**Captioning & Remotion Integration:**

Two Node.js scripts (sub.mjs and sub_v1.mjs) integrate with Remotion to generate and overlay TikTok-style captions onto your videos.

**Streamlit Web Interface:**

A user-friendly Streamlit app (app.py) ties the entire pipeline together, displaying JSON outputs, video previews, and status messages.

**Directory Structure**

```other
andreasink-viralshortsai/
├── ai_video.py                    # Green screen overlay video processing
├── app.py                         # Main Streamlit application
├── media_cache.json               # Cached media analysis results
├── requirements.txt               # Python dependencies
├── sub.mjs                        # Node.js captioning script (Whisper & Remotion)
├── context/
│   └── marketing.md               # Marketing context and product messaging (ExamCram)
├── js-scripts/                    # Remotion-based video rendering and captioning assets
│   ├── package.json
│   ├── remotion.config.ts
│   ├── render.js
│   ├── sub_v1.mjs                 # Alternative Node.js captioning script
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── whisper-config.mjs
│   ├── .eslintrc
│   ├── .prettierrc
│   └── src/
│       ├── Root.tsx               # Entry point for Remotion compositions
│       ├── index.ts               # Remotion registration script
│       ├── load-font.ts           # Custom font loading for captions
│       ├── tailwind.css           # Tailwind CSS configuration
│       └── CaptionedVideo/        # Components for rendering captions over video
│           ├── NoCaptionFile.tsx
│           ├── Page.tsx
│           ├── SubtitlePage.tsx
│           └── index.tsx
└── modules/                       # Python modules for media processing and AI integrations
    ├── broll_suggester.py         # B-roll suggestion based on media analysis
    ├── broller.py                 # Overlay B-roll clips onto the main video
    ├── config.py                  # API key and environment configuration
    ├── directory_reader.py        # Scans media directories for assets
    ├── media_analyzer.py          # Analyzes images and videos using AI
    ├── silence.py                 # Detects silence in transcripts
    ├── silence_trimmer.py         # Trims video segments based on silence detection
    ├── structured_output.py       # Helper for generating AI outputs with a defined schema
    ├── sub.py                     # Alternative captioning/subtitle processing
    ├── video_processor.py         # Orchestrates the video editing pipeline
    ├── voiceover_generator.py     # Generates voiceovers using ElevenLabs TTS
    ├── zoom_effect_creator.py     # Creates JSON configurations for zoom effects
    └── zoomer.py                  # Applies zoom effects to videos using JSON configs
```

**Python Dependencies**

1. Create and activate a virtual environment:

```other
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:

```other
pip install -r requirements.txt
```

**Node.js Dependencies**

1. Navigate to the js-scripts directory:

```other
cd js-scripts
```

2. Install Node.js dependencies:

```other
npm install
```

**Configuration**

**Environment Variables:**

Create a .env file at the root of the project to store your API keys and other sensitive configuration values:

```other
OPENAI_API_KEY=your_openai_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key
# Optionally add your OpenAI organization ID if needed:
OPENAI_ORGANIZATION=your_organization_id
```

**Marketing Context:**

The marketing copy and context for media analysis is located in context/marketing.md. Update this file as needed to tailor suggestions for your specific campaign.

**Whisper & Remotion Configuration:**

Adjust js-scripts/whisper-config.mjs for your desired Whisper model and language settings. Similarly, modify remotion.config.ts if you need to change video output settings.

**Usage**

**Running the Streamlit App**

The main pipeline is accessible via a Streamlit web interface. To start the app, run:

```other
streamlit run app.py
```

This app will:

- Start the Node.js captioning subprocess.
- Load and analyze media files from the specified directory.
- Generate B-roll suggestions and voiceover (if enabled).
- Process videos (silence trimming, zoom effects, captioning) and display the final video output.

**Node.js Captioning Scripts**

There are two captioning scripts included:

**Basic Captioning:**

Run with:

```other
node sub.mjs
```

**Enhanced Captioning (v1):**

Run with:

```other
node sub_v1.mjs
```

These scripts extract audio, transcribe using Whisper, and generate caption JSON files to be consumed by Remotion.

**Video Processing Pipeline**

The core video processing is handled in modules/video_processor.py. This module:

- Detects silence in the video transcript.
- Trims the video based on non-silent segments.
- Integrates zoom effects and B-roll overlays.
- Merges voiceover audio (if provided) with the final video.

Final video outputs are saved to the js-scripts/public directory and can be previewed via the Streamlit app or directly using your preferred video player.

**Dependencies & Requirements**

**Python Packages:**

- moviepy
- opencv-python
- pillow
- streamlit
- openai
- pydantic
- python-dotenv
- markdown2
- elevenlabs
- (and more as listed in requirements.txt)

**Node.js Packages:**
- remotion and related packages (see package.json in js-scripts)
- chokidar (for file watching in captioning scripts)
- Other dependencies as configured in the Node.js scripts.

**External Tools:**

- FFmpeg for media extraction and encoding.

**Contributing**

Contributions are welcome! Feel free to open issues or submit pull requests for improvements or bug fixes. Please adhere to the code style and include detailed comments and tests when applicable.

**Acknowledgments**

- **Remotion:** For providing a flexible framework for video rendering and captioning.
- **OpenAI & ElevenLabs:** For enabling AI-driven media analysis and voice synthesis.

Happy editing and viral video making!


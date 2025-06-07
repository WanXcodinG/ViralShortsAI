import streamlit as st
from pathlib import Path
import shutil
import subprocess
import os
import atexit
import openai
import time
import json
import threading
from modules.config import get_openai_api_key, get_elevenlabs_api_key
from modules.directory_reader import gather_media_files
from modules.media_analyzer import analyze_media_files
from modules.broll_suggester import suggest_broll
from modules.voiceover_generator import generate_voiceover
from modules.video_processor import process_videos

# Path to the sub_v1.mjs script
SUB_SCRIPT_PATH = "/Users/andreas/Desktop/ViralShortAI/viralshortai/js-scripts/sub_v1.mjs"
NODE_EXECUTABLE = "node"  # Ensure Node.js is installed and accessible

# Subprocess handle for managing sub_v1.mjs
subprocess_handle = None

# Global variable to control the automation thread
automation_running = False
automation_thread = None

def start_sub_v1_script():
    """Start the sub_v1.mjs script as a subprocess."""
    global subprocess_handle
    if not subprocess_handle:
        try:
            subprocess_handle = subprocess.Popen(
                [NODE_EXECUTABLE, SUB_SCRIPT_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            st.success("sub_v1.mjs started successfully.")
        except Exception as e:
            st.error(f"Failed to start sub_v1.mjs: {str(e)}")

def stop_sub_v1_script():
    """Stop the sub_v1.mjs subprocess."""
    global subprocess_handle
    if subprocess_handle:
        subprocess_handle.terminate()
        try:
            subprocess_handle.wait(timeout=5)
        except subprocess.TimeoutExpired:
            subprocess_handle.kill()  # Force kill if not terminated
        st.write("sub_v1.mjs stopped.")
        subprocess_handle = None

# Ensure the script is stopped when the app exits
atexit.register(stop_sub_v1_script)

def generate_marketing_content(prompt, context_path, client):
    """Generate marketing content based on user prompt and existing context."""
    if not prompt:
        return None
    
    existing_context = ""
    if context_path.exists():
        existing_context = context_path.read_text()
    
    system_message = """You are a world-class marketing content creator. 
    Your job is to enhance existing marketing content based on the user's prompt.
    Maintain the tone and style of the existing content while incorporating new ideas.
    Output should be in Markdown format."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Existing marketing content:\n{existing_context}\n\nUser prompt: {prompt}\n\nPlease enhance the marketing content based on this prompt."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating marketing content: {str(e)}")
        return existing_context

def generate_voiceover_text(marketing_context, client):
    """Generate voiceover text from marketing context."""
    system_message = """You are a professional voiceover script writer.
    Create a compelling, conversational 30-60 second script for a short promotional video.
    The script should flow naturally when spoken aloud.
    Focus on the key selling points and benefits."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Marketing context:\n{marketing_context}\n\nCreate a voiceover script that promotes this product effectively in a short-form video."}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating voiceover text: {str(e)}")
        return "Your product is amazing. Download it today to experience all its great features."

def save_production_log(log_entry, log_path):
    """Save a log of the production run."""
    if log_path.exists():
        with open(log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def automated_content_generation(project_root, media_dir, context_path, output_dir, client, eleven_api_key, generation_interval=3600):
    """Continuously generate content at specified intervals."""
    global automation_running
    
    while automation_running:
        try:
            st.session_state['status_message'] = "Starting new content generation cycle..."
            
            # Read context
            marketing_context = context_path.read_text()
            
            # Gather and analyze media files
            media_files = gather_media_files(media_dir)
            if not media_files:
                st.session_state['status_message'] = "No media files found. Waiting for next cycle..."
                time.sleep(generation_interval)
                continue
                
            analyzed_media = analyze_media_files(media_files, marketing_context)
            
            # Suggest B-roll
            broll_suggestions = suggest_broll(analyzed_media, marketing_context)
            
            # Generate voiceover
            voiceover_text = generate_voiceover_text(marketing_context, client)
            voiceover_path = output_dir / 'voiceover.mp3'
            generate_voiceover(voiceover_text, str(voiceover_path), eleven_api_key)
            
            # Process Videos
            try:
                final_video_path = process_videos(
                    media_dir,
                    output_dir,
                    broll_suggestions,
                    voiceover_path
                )
                
                # Move the video to the output directory
                destination_path = output_dir / final_video_path.name
                if final_video_path.exists():
                    shutil.move(str(final_video_path), str(destination_path))
                    
                    # Log the production
                    log_entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "media_used": [f.name for f in media_files],
                        "output_file": destination_path.name,
                        "voiceover_text": voiceover_text
                    }
                    save_production_log(log_entry, project_root / "production_log.json")
                    
                    st.session_state['status_message'] = f"Video created successfully: {destination_path.name}"
                else:
                    st.session_state['status_message'] = "Video processing completed but output file not found."
            except Exception as e:
                st.session_state['status_message'] = f"Error in video processing: {str(e)}"
            
            # Wait for the next cycle
            time.sleep(generation_interval)
        except Exception as e:
            st.session_state['status_message'] = f"Error in automation cycle: {str(e)}"
            time.sleep(60)  # Short wait before retrying on error

def start_automation():
    """Start the automation thread."""
    global automation_running, automation_thread
    
    if not automation_running:
        automation_running = True
        
        # Initialize variables needed for automation
        project_root = Path(__file__).parent
        media_dir = project_root / 'media'
        context_path = project_root / 'context' / 'marketing.md'
        output_dir = project_root / 'js-scripts' / 'public'
        output_dir.mkdir(exist_ok=True)
        
        # Set up API clients
        openai_client = openai.OpenAI(api_key=get_openai_api_key())
        eleven_api_key = get_elevenlabs_api_key()
        
        # Start the automation thread
        automation_thread = threading.Thread(
            target=automated_content_generation,
            args=(project_root, media_dir, context_path, output_dir, openai_client, eleven_api_key),
            daemon=True
        )
        automation_thread.start()
        st.session_state['automation_status'] = "Running"
        st.session_state['status_message'] = "Automation started. Content generation will begin shortly."
    else:
        st.warning("Automation is already running.")

def stop_automation():
    """Stop the automation thread."""
    global automation_running
    
    if automation_running:
        automation_running = False
        st.session_state['automation_status'] = "Stopped"
        st.session_state['status_message'] = "Automation stopped."
    else:
        st.warning("Automation is not running.")

def main():
    st.title("Viral Short AI - Automated Video Generation")

    # Initialize session state variables
    if 'automation_status' not in st.session_state:
        st.session_state['automation_status'] = "Stopped"
    if 'status_message' not in st.session_state:
        st.session_state['status_message'] = "Ready to start."

    # Start the sub_v1.mjs script
    start_sub_v1_script()

    # Define paths
    project_root = Path(__file__).parent
    media_dir = project_root / 'media'
    context_path = project_root / 'context' / 'marketing.md'
    output_dir = project_root / 'js-scripts' / 'public'
    output_dir.mkdir(exist_ok=True)

    # User input section
    st.header("Content Configuration")
    
    # Marketing prompt input
    marketing_prompt = st.text_area(
        "Marketing Prompt", 
        "Describe what you want to promote or the angle for your marketing content.",
        help="Enter details about your marketing goals, target audience, and key messages."
    )
    
    # Generation interval selection
    generation_interval = st.slider(
        "Content Generation Interval (hours)", 
        min_value=1, 
        max_value=24, 
        value=3,
        help="How often should new content be generated?"
    )
    
    # Generate button for one-time content creation
    if st.button("Generate Content Now"):
        with st.spinner("Generating content..."):
            # Set up API keys
            client = openai.OpenAI(api_key=get_openai_api_key())
            eleven_api_key = get_elevenlabs_api_key()
            
            # Update marketing content based on prompt
            if marketing_prompt:
                new_marketing_content = generate_marketing_content(marketing_prompt, context_path, client)
                if new_marketing_content:
                    context_path.write_text(new_marketing_content)
                    st.success("Marketing context updated!")
            
            # Read context
            marketing_context = context_path.read_text()
            
            # Gather media files
            media_files = gather_media_files(media_dir)
            if not media_files:
                st.error("No media files found in the media directory.")
                return
                
            analyzed_media = analyze_media_files(media_files, marketing_context)
            st.json([m.dict() for m in analyzed_media])
            
            # Suggest B-roll
            broll_suggestions = suggest_broll(analyzed_media, marketing_context)
            st.json(broll_suggestions)
            
            # Generate voiceover
            voiceover_text = generate_voiceover_text(marketing_context, client)
            st.markdown("### Generated Voiceover Text")
            st.markdown(voiceover_text)
            
            voiceover_path = output_dir / 'voiceover.mp3'
            generate_voiceover(voiceover_text, str(voiceover_path), eleven_api_key)
            st.audio(str(voiceover_path))
            
            # Process Videos
            try:
                final_video_path = process_videos(
                    media_dir,
                    output_dir,
                    broll_suggestions,
                    voiceover_path
                )
                
                # Move the video to the output directory
                destination_path = output_dir / final_video_path.name
                if final_video_path.exists():
                    shutil.move(str(final_video_path), str(destination_path))
                    st.success(f"Video created successfully: {destination_path.name}")
                    
                    # Display the video
                    st.video(str(destination_path))
                    
                    # Log the production
                    log_entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "prompt": marketing_prompt,
                        "media_used": [f.name for f in media_files],
                        "output_file": destination_path.name,
                        "voiceover_text": voiceover_text
                    }
                    save_production_log(log_entry, project_root / "production_log.json")
                else:
                    st.error(f"Generated video not found: {final_video_path}")
            except Exception as e:
                st.error(f"Error in video processing: {str(e)}")
    
    # Automation controls
    st.header("Automation Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Continuous Generation"):
            start_automation()
    
    with col2:
        if st.button("Stop Continuous Generation"):
            stop_automation()
    
    # Status display
    st.subheader("Automation Status")
    status_indicator = "🟢" if st.session_state['automation_status'] == "Running" else "🔴"
    st.markdown(f"{status_indicator} **{st.session_state['automation_status']}**")
    st.markdown(f"Status: {st.session_state['status_message']}")
    
    # Recent productions
    st.header("Recent Productions")
    log_path = project_root / "production_log.json"
    if log_path.exists():
        with open(log_path, 'r') as f:
            logs = json.load(f)
        
        # Display the 5 most recent logs
        for log in logs[-5:]:
            with st.expander(f"{log['timestamp']}"):
                st.write(f"**Prompt:** {log.get('prompt', 'N/A')}")
                st.write(f"**Media Used:** {', '.join(log['media_used'])}")
                st.write(f"**Output File:** {log['output_file']}")
                video_path = output_dir / log['output_file']
                if video_path.exists():
                    st.video(str(video_path))

if __name__ == "__main__":
    main()
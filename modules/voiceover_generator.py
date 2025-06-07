from elevenlabs.client import ElevenLabs
import streamlit as st
import os
import requests
import tempfile
from pathlib import Path

def generate_voiceover(
    text: str,
    output_path: str,
    api_key: str,
    voice_name: str = "Rachel",  # Default voice, can be changed
    model: str = "eleven_multilingual_v2"  # Default model, can also be changed
):
    """
    Generates a voiceover audio file from the given text using ElevenLabs TTS.
    
    Parameters:
    - text (str): The text to be converted into speech.
    - output_path (str): The file path where the audio file will be saved.
    - api_key (str): Your ElevenLabs API key.
    - voice_name (str): Name or ID of the voice to use (default: "Rachel").
    - model (str): The ElevenLabs model to use for generation (default: "eleven_multilingual_v2").
    """
    if not api_key:
        st.warning("ElevenLabs API key not set. Using fallback TTS method.")
        return generate_fallback_tts(text, output_path)

    try:
        # Initialize the ElevenLabs client with your API key
        client = ElevenLabs(api_key=api_key)

        # Generate the audio bytes from text
        # Note: 'generate' returns raw audio bytes if stream=False (default).
        audio = client.generate(
            text=text,
            voice=voice_name,
            model=model
        )

        # Save the audio to a file
        with open(output_path, 'wb') as f:
            f.write(audio)

        print(f"Voiceover generated and saved to {output_path}")
        return True
    except Exception as e:
        st.error(f"Error generating voiceover with ElevenLabs: {str(e)}")
        return generate_fallback_tts(text, output_path)

def generate_fallback_tts(text: str, output_path: str):
    """
    Fallback method for generating TTS using a free API if ElevenLabs fails.
    """
    try:
        # Use a free TTS service as fallback
        url = "https://api.streamelements.com/kappa/v2/speech"
        params = {
            "voice": "Brian", 
            "text": text[:500]  # Most free APIs have text limits
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Fallback TTS generated and saved to {output_path}")
            return True
        else:
            raise Exception(f"Fallback TTS API error: {response.status_code}")
    except Exception as e:
        st.error(f"Error with fallback TTS: {str(e)}")
        # Last resort: Create a silent audio file to prevent pipeline failure
        create_silent_audio(output_path, duration=10)  # 10 seconds of silence
        return False

def create_silent_audio(output_path: str, duration: int = 10):
    """
    Create a silent audio file as a last resort to ensure the pipeline doesn't fail.
    Uses ffmpeg if available, otherwise creates an empty file.
    """
    try:
        import subprocess
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        # Use ffmpeg to create silent audio
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=stereo', 
            '-t', str(duration), '-q:a', '9', '-acodec', 'libmp3lame', 
            temp_file.name
        ], check=True, capture_output=True)
        
        # Copy the temp file to the desired output path
        Path(temp_file.name).rename(output_path)
        os.remove(temp_file.name)
        print(f"Created silent audio at {output_path}")
        return True
    except Exception as e:
        print(f"Failed to create silent audio: {e}")
        # As a last resort, create an empty file
        with open(output_path, 'wb') as f:
            f.write(b'')
        return False
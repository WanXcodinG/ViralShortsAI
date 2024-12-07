from elevenlabs.client import ElevenLabs

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
# Provides configuration utilities, such as retrieving API keys.

import os
from dotenv import load_dotenv

def get_openai_api_key():
    load_dotenv()
    # Retrieve OpenAI API key from environment or a secure config
    return os.getenv("OPENAI_API_KEY")

def get_elevenlabs_api_key():
    load_dotenv()
    # Retrieve Eleven Labs API key from environment or a secure config
    return os.getenv("ELEVEN_LABS_API_KEY")
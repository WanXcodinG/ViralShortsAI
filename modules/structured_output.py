# Utility for generating structured outputs via the OpenAI API.
# This is an optional helper if you prefer a more reliable structured output approach.

import json
import openai
import os
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, ValidationError
import streamlit as st

def generate_structured_output(
    system_prompt: str, 
    model_class: Type[BaseModel], 
    messages: List[Dict[str, str]],
    max_retries: int = 2
) -> Optional[BaseModel]:
    """
    Generate structured output from OpenAI API and convert it to a Pydantic model.
    
    Args:
        system_prompt: The system prompt to use for the OpenAI API.
        model_class: The Pydantic model class to convert the output to.
        messages: The list of messages for the OpenAI API.
        max_retries: Maximum number of retries on failure.
    
    Returns:
        An instance of the Pydantic model, or None if unsuccessful.
    """
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Skipping structured output generation.")
        return None
    
    # Initialize the client
    client = openai.OpenAI(api_key=api_key)
    
    # Add system prompt to messages
    full_messages = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)
    
    # Try to generate the structured output
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=full_messages,
                temperature=0.2,  # Lower temperature for more consistent outputs
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            response_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                response_json = json.loads(response_text)
                
                # Try to instantiate the Pydantic model
                try:
                    model_instance = model_class.parse_obj(response_json)
                    return model_instance
                except ValidationError as ve:
                    # On validation error, add more guidance and retry
                    if attempt < max_retries:
                        schema = model_class.schema()
                        schema_str = json.dumps(schema, indent=2)
                        error_msg = f"Validation failed: {str(ve)}. Please conform to this schema: {schema_str}"
                        full_messages.append({"role": "user", "content": error_msg})
                        continue
                    else:
                        print(f"Failed to validate model after {max_retries} attempts: {ve}")
                        return None
                        
            except json.JSONDecodeError as je:
                # On JSON parse error, add more guidance and retry
                if attempt < max_retries:
                    error_msg = f"Invalid JSON: {str(je)}. Please return only valid JSON that conforms to the model schema."
                    full_messages.append({"role": "user", "content": error_msg})
                    continue
                else:
                    print(f"Failed to parse JSON after {max_retries} attempts: {je}")
                    return None
                    
        except Exception as e:
            # Handle API errors or other unexpected errors
            print(f"Error calling OpenAI API: {str(e)}")
            return None
    
    return None

def parse_structured_output(output_text: str, model_class: Type[BaseModel]) -> Optional[BaseModel]:
    """
    Parse a string as JSON and convert it to a Pydantic model.
    
    Args:
        output_text: The text to parse as JSON.
        model_class: The Pydantic model class to convert the output to.
    
    Returns:
        An instance of the Pydantic model, or None if unsuccessful.
    """
    try:
        # Try to parse as JSON
        json_data = json.loads(output_text)
        
        # Try to instantiate the Pydantic model
        return model_class.parse_obj(json_data)
    except json.JSONDecodeError as je:
        print(f"Failed to parse as JSON: {je}")
        return None
    except ValidationError as ve:
        print(f"Failed to validate model: {ve}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing output: {e}")
        return None
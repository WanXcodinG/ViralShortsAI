# Utility for generating structured outputs via the OpenAI API.
# This is an optional helper if you prefer a more reliable structured output approach.

import openai
import json
from pydantic import BaseModel, ValidationError
from typing import List

def generate_structured_output(prompt: str, model_class: BaseModel, messages = []):
    try:
        system_prompt = {"role": "system", "content": prompt}
        user_message = {"role": "user", "content": "JSON: "}
        completion = openai.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[system_prompt] + messages + [user_message],
            response_format=model_class,
        )
        structured_output = completion.choices[0].message
        parsed_content = json.loads(structured_output.content)
        return model_class(**parsed_content)
    except (ValidationError, json.JSONDecodeError) as ve:
        print(f"Validation or JSON decoding error in generate_structured_output: {ve}")
        return None
    except Exception as e:
        print(f"Error in generate_structured_output: {e}")
        if hasattr(e, 'response'):
            print("Raw API response:", e.response)
        return None
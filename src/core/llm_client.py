import os
import asyncio
from typing import Any, Type
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types
from config.settings import MAX_RETRIES, BASE_RETRY_DELAY
from dotenv import load_dotenv

load_dotenv()


class LlmAgent:
    def __init__(self, model: str = "gemini-2.0-flash", system_prompt: str = "", output_type: Type[BaseModel] = None):
        """
        Initializes the LLM Agent using Google Gemini API.
        
        Args:
            model: Model name (e.g., 'gemini-2.0-flash').
            system_prompt: System instruction.
            output_type: Pydantic model class for structured output.
        """
        self.model_name = model
        self.system_prompt = system_prompt
        self.output_type = output_type
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found. Please set it in your .env file.")
        
        self.client = genai.Client(api_key=api_key)

    def run(self, prompt: str) -> Any:
        """
        Executes the prompt and returns a structured object using Gemini's structured output.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    response_mime_type="application/json",
                    response_schema=self.output_type,
                )
            )
            
            # Parse the JSON response into the Pydantic model
            import json
            data = json.loads(response.text)
            
            # Inject usage metadata if available
            if response.usage_metadata:
                data["tokens_input"] = response.usage_metadata.prompt_token_count
                data["tokens_output"] = response.usage_metadata.candidates_token_count
                
            return self.output_type(**data)
            
        except Exception as e:
            print(f"Error in LlmAgent run (Gemini): {e}")
            raise e

    async def async_run(self, prompt: str) -> Any:
        """
        Executes the prompt asynchronously with retry logic for rate limits.
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        response_mime_type="application/json",
                        response_schema=self.output_type,
                    )
                )
                
                # Parse the JSON response into the Pydantic model
                import json
                data = json.loads(response.text)
                
                # Inject usage metadata if available
                if response.usage_metadata:
                    data["tokens_input"] = response.usage_metadata.prompt_token_count
                    data["tokens_output"] = response.usage_metadata.candidates_token_count
                    
                return self.output_type(**data)
                
            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str or "quota" in error_str or "429" in error_str:
                    if attempt < MAX_RETRIES - 1:
                        delay = BASE_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                        await asyncio.sleep(delay)
                    else:
                        print(f"Rate limit exceeded after {MAX_RETRIES} retries")
                        raise e
                else:
                    print(f"Error in LlmAgent async_run (Gemini): {e}")
                    raise e

class LoopAgent:
    def __init__(self, agent, **kwargs):
        self.agent = agent

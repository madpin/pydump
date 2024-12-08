import os
from typing import Dict
import aiohttp
from generators.base import BaseGenerator, GenerationResult
from config.models import ModelConfig


class DalleGenerator(BaseGenerator):
    def _get_headers(self) -> dict:
        api_key = os.getenv(self.model_config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found for {self.model_config.name}")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate(self, prompt: str, parameters: Dict) -> GenerationResult:
        payload = {
            "prompt": prompt,
            "n": 1,
            **parameters,
        }
        api_response = await self._send_request(payload)

        if api_response:
            try:
                images = [image_data["url"] for image_data in api_response["data"]]
                return GenerationResult(success=True, images=images)
            except (KeyError, IndexError, TypeError):
                self._log_api_error(api_response, payload)
                return GenerationResult(
                    success=False, error_message="Invalid API response format"
                )
        else:
            self._log_api_error(api_response, payload)
            return GenerationResult(
                success=False, error_message=api_response.get("error_message")
            )

import os
from typing import Dict
import aiohttp
from generators.base import BaseGenerator, GenerationResult
from config.models import ModelConfig


class FluxProGenerator(BaseGenerator):
    def _get_headers(self) -> dict:
        api_key = os.getenv(self.model_config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found for {self.model_config.name}")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def generate(self, prompt: str, parameters: Dict) -> GenerationResult:
        payload = {"prompt": prompt, **parameters}
        api_response = await self._send_request(payload)

        if api_response:
            try:
                image_url = api_response.get("image_url")
                if image_url and api_response.get("status") == "ok":
                    return GenerationResult(success=True, images=[image_url])
                else:
                    self._log_api_error(api_response, payload)
                    return GenerationResult(
                        success=False,
                        error_message="Image URL not found in API response",
                    )
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

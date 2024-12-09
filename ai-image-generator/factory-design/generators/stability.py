import os
import json
from typing import Dict
import aiohttp
from generators.base import BaseGenerator, GenerationResult
import logging

logger = logging.getLogger(__name__)


class StabilityGenerator(BaseGenerator):
    """Generator class for Stability AI's image generation API."""

    def _get_headers(self) -> dict:
        """
        Get headers for API request.

        Returns:
            dict: Headers including authorization.

        Raises:
            ValueError: If API key is not found in environment variables.
        """
        api_key = os.getenv(self.model_config.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found for {self.model_config.name}")
        return {
            "Authorization": f"Bearer {api_key}",
            "accept": "image/*",
            # "Content-Type": "multipart/form-data",
        }

    async def _send_request(self, payload: Dict) -> Dict:
        """
        Send generation request to Stability AI API using multipart/form-data.

        Args:
            payload (Dict): Request payload containing generation parameters.

        Returns:
            Dict: API response or error message.
        """
        async with aiohttp.ClientSession() as session:
            try:
                headers = self._get_headers()

                # Prepare the form data
                # data = aiohttp.FormData()
                # data = aiohttp.MultipartWriter('form-data')

                # # Add text prompts
                # # data.append("text_prompts[0][text]", payload["prompt"])
                # # data.append("text_prompts[0][weight]", "1")

                # # Add negative prompt if present
                # # if payload.get("negative_prompt"):
                # #     data.append("text_prompts[1][text]", payload["negative_prompt"])
                # #     data.append("text_prompts[1][weight]", "-1")

                # # # Add other parameters
                # # data.append("cfg_scale", str(payload.get("cfg_scale", 7)))
                # # data.append("height", str(payload.get("height", 512)))
                # # data.append("width", str(payload.get("width", 512)))
                # # data.append("samples", str(payload.get("num_images", 1)))
                # # data.append("steps", str(payload.get("steps", 30)))
                # # data.append("files", {"none": ""})
                # data.append("output_format", "jpeg")
                # data.append("prompt", "a banana")
                # if "seed" in payload:
                #     data.append("seed", str(payload["seed"]))

                data = aiohttp.FormData(quote_fields=False)

                data.add_field("prompt", payload["prompt"])
                data.add_field("output_format", "jpeg")

                headers.update(data.headers)

                async with session.post(
                    str(self.model_config.endpoint),
                    headers=headers,
                    data=data,
                    timeout=60,
                ) as response:
                    if response.status == 429:
                        logger.warning(
                            "Rate limit exceeded. Please wait and try again."
                        )
                        return {"error_message": "Rate limit exceeded"}

                    response_json = await response.json()

                    if response.status != 200:
                        logger.error(
                            f"API returned status {response.status}: {response_json}"
                        )
                        return {"error_message": f"API error: {response_json}"}

                    return response_json

            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {str(e)}")
                return {"error_message": f"Request failed: {str(e)}"}

    def _log_api_error(self, response: Dict, payload: Dict) -> None:
        """
        Log API errors with context.

        Args:
            response (Dict): API response containing error details
            payload (Dict): Original request payload
        """
        logger.error(
            f"API Error for {self.model_config.name}:\n"
            f"Payload: {payload}\n"
            f"Response: {response}"
        )

    async def generate(self, prompt: str, parameters: Dict) -> GenerationResult:
        """
        Generate images using Stability AI API.

        Args:
            prompt (str): Text prompt for image generation
            parameters (Dict): Additional parameters for generation

        Returns:
            GenerationResult: Object containing success status and either images or error message
        """
        payload = {
            "prompt": prompt,
            "output_format": "jpeg",
        }
        payload.update(parameters)

        api_response = await self._send_request(payload)

        if not api_response:
            self._log_api_error(api_response, payload)
            return GenerationResult(success=False, error_message="No response from API")

        try:
            if "artifacts" in api_response:
                images = api_response.get("artifacts", [])
                if not images:
                    self._log_api_error(api_response, payload)
                    return GenerationResult(
                        success=False, error_message="No images generated"
                    )
                return GenerationResult(success=True, images=images)
            else:
                self._log_api_error(api_response, payload)
                return GenerationResult(
                    success=False,
                    error_message=api_response.get("error_message", "Unknown error"),
                )
        except Exception as e:
            self._log_api_error(api_response, payload)
            logger.error(f"Error processing API response: {str(e)}")
            return GenerationResult(
                success=False, error_message=f"Error processing response: {str(e)}"
            )

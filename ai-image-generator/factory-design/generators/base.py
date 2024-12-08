import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Dict
from pydantic import BaseModel, ValidationError
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class GenerationResult(BaseModel):
    """
    A model representing the result of an image generation request.

    Attributes:
        success (bool): Whether the generation was successful
        error_message (Optional[str]): Error message if generation failed
        images (Optional[List[str]]): List of generated image URLs or paths
    """

    success: bool
    error_message: Optional[str] = None
    images: Optional[List[str]] = None


class BaseGenerator(ABC):
    """
    Abstract base class for image generators.

    This class provides the basic structure and common functionality for
    different image generation implementations.

    Attributes:
        model_config: Configuration for the specific model
        headers (Dict): HTTP headers for API requests
    """

    def __init__(self, model_config):
        """
        Initialize the generator with model configuration.

        Args:
            model_config: Configuration object for the model
        """
        self.model_config = model_config
        self.headers = self._get_headers()

    @abstractmethod
    def _get_headers(self) -> Dict:
        """
        Get headers for API requests.

        Returns:
            Dict: Headers to be used in API requests
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str, parameters: Dict) -> GenerationResult:
        """
        Generate images based on the provided prompt and parameters.

        Args:
            prompt (str): Text prompt for image generation
            parameters (Dict): Additional parameters for generation

        Returns:
            GenerationResult: Result of the generation attempt
        """
        pass

    async def _send_request(self, payload: Dict) -> Optional[dict]:
        """
        Send HTTP request to the API endpoint.

        Args:
            payload (Dict): Request payload

        Returns:
            Optional[dict]: Response from the API or error information
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    str(self.model_config.endpoint),
                    headers=self.headers,
                    json=payload,
                    timeout=120,
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_details = await response.text()
                        return {
                            "success": False,
                            "error_message": f"""API request failed with status {response.status}.\n
Response body: {error_details}.\n
Endpoint: {self.model_config.endpoint}""",
                        }

            except aiohttp.ClientError as e:
                return {"success": False, "error_message": f"API request failed: {e}"}
            except Exception as e:
                return {
                    "success": False,
                    "error_message": f"An unexpected error occurred: {e}",
                }

    # Add this method to ModelConfig class
    def _log_api_error(self, response, payload):
        error_detail = {
            "request_payload": payload,
            "response": response,
        }

        # Save response to JSON file
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        with open(data_dir / "last_response.json", "w", encoding="utf-8") as f:
            json.dump(response, f, indent=4, ensure_ascii=False)

        def truncate_dict_values(d, max_length=500):
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    result[key] = truncate_dict_values(value, max_length)
                elif isinstance(value, str):
                    if len(value) > max_length:
                        result[key] = value[:max_length] + " (...) " + value[-50:]
                    else:
                        result[key] = value
                else:
                    result[key] = value
            return result

        error_detail = truncate_dict_values(error_detail)

        logger.error(
            "API Error Details:\n"
            + "\n".join([f"  {key}: {value}" for key, value in error_detail.items()])
        )

    def validate_parameters(self, parameters: Dict) -> bool:
        """
        Validate generation parameters.

        Args:
            parameters (Dict): Parameters to validate

        Returns:
            bool: True if parameters are valid, error dict otherwise
        """
        try:
            # This needs to be implemented in each generator to validate specific parameters
            return True
        except ValidationError as e:
            return {
                "success": False,
                "error_message": f"Parameter validation failed: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "error_message": f"An unexpected error occurred during parameter validation: {e}",
            }

"""
Image Generation Web App using Multiple AI Models

Description:
    A Streamlit web application that allows users to generate images using different AI models
    (Stability AI SD3.5, FLUX-pro, and DALL-E). The app saves generation history to an SQLite database
    and provides a comprehensive interface for model selection and parameter configuration.

Features:
    - Multiple model selection
    - Customizable generation parameters
    - Generation history tracking
    - Image preview and download
    - Parameter persistence

Required Environment Variables:
    - DEEPINFRA_API_KEY: API key for DeepInfra (Stability AI and FLUX-pro)
    - OPENAI_API_KEY: API key for DALL-E

Required Packages:
    - streamlit
    - requests
    - pillow
    - pandas
    - sqlite3
    - python-dotenv

Usage:
    streamlit run app.py

Author:
    tpinto
"""

import os
import json
import base64
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st
import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Constants and Configuration ---

MODELS = {
    "stabilityai/sd3.5": {
        "endpoint": "https://api.deepinfra.com/v1/inference/stabilityai/sd3.5",
        "api_key": os.getenv("DEEPINFRA_API_KEY"),
        "type": "stability",
        "parameters": {
            "negative_prompt": {
                "type": "text_area",
                "label": "Negative Prompt",
                "default": "",
                "help": "Negative text prompt",
            },
            "num_images": {
                "type": "slider",
                "label": "Number of Images",
                "min": 1.0,
                "max": 4.0,
                "default": 1.0,
                "help": "Number of images to generate",
            },
            "num_inference_steps": {
                "type": "slider",
                "label": "Inference Steps",
                "min": 1.0,
                "max": 50.0,
                "default": 35.0,
                "help": "Number of denoising steps",
            },
            "aspect_ratio": {
                "type": "selectbox",
                "label": "Aspect Ratio",
                "options": [
                    "1:1",
                    "16:9",
                    "21:9",
                    "3:2",
                    "2:3",
                    "4:5",
                    "5:4",
                    "9:16",
                    "9:21",
                ],
                "default": "1:1",
                "help": "Defines width and height ratio",
            },
            "guidance_scale": {
                "type": "slider",
                "label": "Guidance Scale",
                "min": 0.0,
                "max": 20.0,
                "default": 7.0,
                "help": "Classifier-free guidance, higher means follow prompt more closely",
            },
            "seed": {
                "type": "number_input",
                "label": "Seed",
                "min": 0,
                "max": 18446744073709551615,
                "default": 0,
                "help": "Random seed, 0 means random",
            },
            "webhook": {
                "type": "text_input",
                "label": "Webhook URL",
                "default": "",
                "help": "Webhook to call when inference is done (optional)",
            },
        },
    },
    "black-forest-labs/FLUX-pro": {
        "endpoint": "https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-pro",
        "api_key": os.getenv("DEEPINFRA_API_KEY"),
        "type": "flux",
        "parameters": {
            "width": {
                "type": "slider",
                "label": "Width",
                "min": 256.0,
                "max": 1440.0,
                "default": 1024.0,
                "step": 32.0,
                "help": "Width of the generated image in pixels",
            },
            "height": {
                "type": "slider",
                "label": "Height",
                "min": 256.0,
                "max": 1440.0,
                "default": 1024.0,
                "step": 32.0,
                "help": "Height of the generated image in pixels",
            },
            "prompt_upsampling": {
                "type": "checkbox",
                "label": "Prompt Upsampling",
                "default": False,
                "help": "Automatically modifies the prompt for more creative generation",
            },
            "safety_tolerance": {
                "type": "slider",
                "label": "Safety Tolerance",
                "min": 0.0,
                "max": 6.0,
                "default": 2.0,
                "help": "Tolerance level for moderation (0: strict, 6: least strict)",
            },
            "seed": {
                "type": "number_input",
                "label": "Seed",
                "default": None,
                "help": "Seed for reproducibility (optional)",
            },
            "webhook": {
                "type": "text_input",
                "label": "Webhook URL",
                "default": "",
                "help": "Webhook to call when inference is done (optional)",
            },
        },
    },
    "DALL-E": {
        "endpoint": "https://api.openai.com/v1/images/generations",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "type": "dalle",
        "parameters": {
            "n": {
                "type": "slider-int",
                "label": "Number of Images",
                "min": 1,
                "max": 10,
                "default": 1,
                "help": "Number of images to generate",
            },
            "size": {
                "type": "selectbox",
                "label": "Image Size",
                "options": ["1024x1024", "1024x1792", "1792x1024"],
                "default": "1024x1024",
                "help": "Size of the generated images",
            },
            "quality": {
                "type": "selectbox",
                "label": "Quality",
                "options": ["standard", "hd"],
                "default": "standard",
                "help": "Quality of the generated images",
            },
            "model": {
                "type": "selectbox",
                "options": ["dall-e-3", "dall-e-2"],
                "label": "Model",
                "default": "dall-e-3",
                "help": "DALL-E model version",
            },
        },
    },
}

# --- Database Management ---

class DatabaseManager:
    """Handles all database operations for the application."""

    def __init__(self, db_path: str = "image_generation_history.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model TEXT,
                    prompt TEXT,
                    parameters TEXT,
                    image_path TEXT
                )
            """
            )

    def save_generation(
        self, model: str, prompt: str, parameters: Dict, image_path: str
    ):
        """Save a generation record to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO generation_history (model, prompt, parameters, image_path) VALUES (?, ?, ?, ?)",
                (model, prompt, json.dumps(parameters), image_path),
            )

    def get_history(self, limit: int = 10) -> List[Tuple]:
        """Retrieve generation history from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM generation_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return cursor.fetchall()

# --- Image Generation ---

class ImageGenerator:
    """Handles image generation requests for different AI models."""

    @staticmethod
    def _send_request(
        endpoint: str, headers: Dict, payload: Dict
    ) -> Optional[requests.Response]:
        """Sends a POST request to the specified endpoint and handles errors."""
        try:
            response = requests.post(
                endpoint, headers=headers, json=payload, timeout=120
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e.response, 'json'):
                try:
                    error_detail = f"\nAPI Error Details: {e.response.json()}"
                except:
                    error_detail = f"\nAPI Error Text: {e.response.text}"
            st.error(f"API request failed: {str(e)}{error_detail}")
            return None

    @staticmethod
    def generate_stability(prompt: str, parameters: Dict) -> Optional[str]:
        """Generate image using Stability AI models."""
        headers = {
            "Authorization": f"bearer {MODELS['stabilityai/sd3.5']['api_key']}",
            "Content-Type": "application/json",
        }

        payload = {"prompt": prompt, **parameters}
        response = ImageGenerator._send_request(
            MODELS["stabilityai/sd3.5"]["endpoint"], headers, payload
        )

        if response:
            try:
                return response.json()["images"][0]
            except (KeyError, IndexError) as e:
                st.error(f"Failed to extract image from API response: {str(e)}")
                st.error(f"Response content: {response.text}")
        return None

    @staticmethod
    def generate_flux(prompt: str, parameters: Dict) -> Optional[str]:
        """Generate image using FLUX models."""
        headers = {
            "Authorization": f"bearer {MODELS['black-forest-labs/FLUX-pro']['api_key']}",
            "Content-Type": "application/json",
        }

        payload = {"prompt": prompt, **parameters}
        response = ImageGenerator._send_request(
            MODELS["black-forest-labs/FLUX-pro"]["endpoint"], headers, payload
        )

        if response:
            try:
                result = response.json()
                if result["status"] == "ok":
                    return result["image_url"]
                else:
                    st.warning(f"Generation status: {result['status']}")
                    st.error(f"Full response: {result}")
            except KeyError as e:
                st.error(f"Failed to extract image URL from API response: {str(e)}")
                st.error(f"Response content: {response.text}")
        return None

    @staticmethod
    def generate_dalle(prompt: str, parameters: Dict) -> Optional[List[str]]:
        """Generate image using DALL-E."""
        headers = {
            "Authorization": f"Bearer {MODELS['DALL-E']['api_key']}",
            "Content-Type": "application/json",
        }
        # Add the prompt directly into the parameters
        dalle_parameters = {**parameters, "prompt": prompt}

        # st.write("DALL-E Request Parameters:", dalle_parameters)
        
        response = ImageGenerator._send_request(
            MODELS["DALL-E"]["endpoint"], headers, dalle_parameters
        )

        if response:
            try:
                response_json = response.json()
                # st.write("DALL-E Response:", response_json)
                image_urls = [item["url"] for item in response_json["data"]]
                return image_urls
            except (KeyError, IndexError) as e:
                st.error(f"Failed to extract image URL from API response: {str(e)}")
                st.error(f"Response content: {response.text}")
        return None

# --- Streamlit UI ---

def configure_parameters(model_name: str, key_prefix: str) -> Dict:
    """Configures and displays the parameters for the selected model.

    Args:
        model_name: The name of the model.
        key_prefix: A unique prefix for the Streamlit widget keys.

    Returns:
        A dictionary containing the configured parameters.
    """
    model_config = MODELS[model_name]
    parameters = {}

    with st.expander(f"{model_name} Parameters", expanded=True):
        for param_name, param_config in model_config["parameters"].items():
            widget_key = f"{key_prefix}_{param_name}"  # Create a unique key

            if param_config["type"] == "text_area":
                parameters[param_name] = st.text_area(
                    param_config["label"],
                    value=param_config["default"],
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "slider":
                # Ensure all slider values are floats
                parameters[param_name] = st.slider(
                    param_config["label"],
                    min_value=float(param_config["min"]),
                    max_value=float(param_config["max"]),
                    value=float(param_config["default"]),
                    step=float(param_config.get("step", 1.0)),
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "slider-int":
                # Ensure all slider values are floats
                parameters[param_name] = st.slider(
                    param_config["label"],
                    min_value=int(param_config["min"]),
                    max_value=int(param_config["max"]),
                    value=int(param_config["default"]),
                    step=int(param_config.get("step", 1)),
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "selectbox":
                parameters[param_name] = st.selectbox(
                    param_config["label"],
                    options=param_config["options"],
                    index=param_config["options"].index(param_config["default"]),
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "number_input":
                parameters[param_name] = st.number_input(
                    param_config["label"],
                    value=param_config["default"],
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "checkbox":
                parameters[param_name] = st.checkbox(
                    param_config["label"],
                    value=param_config["default"],
                    help=param_config["help"],
                    key=widget_key,
                )
            elif param_config["type"] == "text_input":
                parameters[param_name] = st.text_input(
                    param_config["label"],
                    value=param_config["default"],
                    help=param_config["help"],
                    key=widget_key,
                )

    # Remove parameters with empty values
    return {k: v for k, v in parameters.items() if v is not None and v != ""}

def display_history(db_manager: DatabaseManager):
    """Displays the generation history."""
    with st.expander("Generation History"):
        history = db_manager.get_history()
        for record in history:
            st.write(f"**Model:** {record[2]}")
            st.write(f"**Prompt:** {record[3]}")
            st.write(f"**Parameters:** {record[4]}")
            st.image(record[5])
            st.divider()

def main():
    """Main function to run the Streamlit app."""
    st.title("AI Image Generator")

    # Initialize database manager
    db_manager = DatabaseManager()

    # Model selection
    selected_models = st.multiselect(
        "Select AI Models", list(MODELS.keys()), default=list(MODELS.keys())[0]
    )

    # Common parameters
    prompt = st.text_area("Enter your prompt", height=100)

    # Configure parameters for selected models
    model_parameters = {}
    for model_name in selected_models:
        model_parameters[model_name] = configure_parameters(model_name, model_name)

    if st.button("Generate Images"):
        if not prompt:
            st.error("Please enter a prompt.")
            return

        for model_name in selected_models:
            st.subheader(f"Generating with {model_name}")
            parameters = model_parameters[model_name]

            try:
                if MODELS[model_name]["type"] == "stability":
                    image_data = ImageGenerator.generate_stability(prompt, parameters)
                    if image_data:
                        db_manager.save_generation(
                            model_name, prompt, parameters, image_data
                        )
                        st.image(image_data)
                        st.download_button(
                            label="Download Image",
                            data=image_data,
                            file_name=f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png",
                        )
                    else:
                        st.error(f"Failed to generate image with {model_name}.")
                elif MODELS[model_name]["type"] == "flux":
                    image_data = ImageGenerator.generate_flux(prompt, parameters)
                    if image_data:
                        db_manager.save_generation(
                            model_name, prompt, parameters, image_data
                        )
                        st.image(image_data)
                        st.download_button(
                            label="Download Image",
                            data=image_data,
                            file_name=f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png",
                        )
                    else:
                        st.error(f"Failed to generate image with {model_name}.")
                elif MODELS[model_name]["type"] == "dalle":
                    image_urls = ImageGenerator.generate_dalle(prompt, parameters)
                    if image_urls:
                        for image_url in image_urls:
                            db_manager.save_generation(
                                model_name, prompt, parameters, image_url
                            )
                            st.image(image_url)
                            # Convert URL to image data for download
                            image_data = requests.get(image_url).content
                            st.download_button(
                                label="Download Image",
                                data=image_data,
                                file_name=f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png",
                            )
                    else:
                        st.error(f"Failed to generate image with {model_name}.")
                else:
                    st.error(f"Unknown model type: {MODELS[model_name]['type']}")
                    continue

            except Exception as e:
                st.error(f"Error generating image with {model_name}: {e}")

    # Display history
    display_history(db_manager)

if __name__ == "__main__":
    main()

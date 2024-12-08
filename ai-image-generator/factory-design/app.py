"""
AI Image Generator Web Application

Description:
    A Streamlit web application for generating images using various AI models. Supports multiple
    model selection, customizable parameters, generation history tracking, and image download.

Features:
    - Multiple model selection
    - Customizable generation parameters
    - Generation history tracking
    - Image preview and download
    - Parameter validation
    - Asynchronous operations for improved responsiveness

Required Environment Variables:
    - DEEPINFRA_API_KEY: API key for DeepInfra models
    - OPENAI_API_KEY: API key for DALL-E

Required Packages:
    - streamlit
    - requests
    - Pillow
    - pydantic
    - python-dotenv
    - aiohttp
    - sqlite3

Usage:
    streamlit run app.py

Author:
    tpinto
"""

import asyncio
import logging
from typing import Dict, List

import streamlit as st
from dotenv import load_dotenv

from config.models import ModelRegistry
from database.manager import DatabaseManager
from generators.factory import create_generator
from ui.components import configure_parameters, display_history

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logging.getLogger("generators").setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()


def initialize_page() -> None:
    """Configure initial Streamlit page settings."""
    st.set_page_config(
        page_title="AI Image Generator",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🎨 AI Image Generator")
    st.markdown("*Transform your ideas into stunning images using AI*")


async def generate_images(
    model_name: str,
    prompt: str,
    parameters: Dict,
    db_manager: DatabaseManager,
) -> None:
    """
    Generate images for a specific model and handle the results.

    Args:
        model_name: Name of the AI model
        prompt: User input prompt
        parameters: Model-specific parameters
        db_manager: Database manager instance
    """
    model_config = ModelRegistry.get_model(model_name)
    if not model_config:
        st.error(f"❌ Model configuration not found for {model_name}")
        return

    generator = create_generator(model_config)
    if not generator.validate_parameters(parameters):
        st.error(f"⚠️ Invalid parameters for {model_name}")
        return

    try:
        result = await generator.generate(prompt, parameters)
        if not result.success:
            st.error(f"❌ Image generation failed for {model_name}: {result.error_message}")
            return

        st.success(f"✨ Image generated successfully with {model_name}!")
        display_generated_images(result.images, model_name, prompt, parameters, db_manager)

    except Exception as e:
        logger.error(f"Error generating images for {model_name}: {str(e)}")
        st.error(f"❌ Unexpected error with {model_name}: {str(e)}")


def display_generated_images(
    images: List,
    model_name: str,
    prompt: str,
    parameters: Dict,
    db_manager: DatabaseManager,
) -> None:
    """
    Display generated images with download buttons.

    Args:
        images: List of generated images
        model_name: Name of the AI model
        prompt: User input prompt
        parameters: Model-specific parameters
        db_manager: Database manager instance
    """
    image_cols = st.columns(len(images))
    for idx, image in enumerate(images):
        db_manager.save_generation(model_name, prompt, parameters, image)
        with image_cols[idx]:
            st.image(
                image,
                use_container_width=True,
                caption=f"Image {idx + 1}",
            )
            st.download_button(
                label="📥 Download",
                data=image,
                file_name=f"generated_image_{model_name}_{idx + 1}.png",
                mime="image/png",
            )


def render_model_selection() -> tuple[str, Dict]:
    """
    Render model selection and parameter configuration UI.

    Returns:
        tuple: User prompt and model parameters dictionary
    """
    available_models = ModelRegistry.get_all_models()
    selected_model_names = st.multiselect(
        "🤖 Select AI Models",
        options=[model.name for model in available_models],
        default=available_models[0].name if available_models else None,
    )

    prompt = st.text_area("✍️ Enter your prompt", height=100)

    model_parameters = {}
    for model_name in selected_model_names:
        model_config = ModelRegistry.get_model(model_name)
        if model_config:
            st.markdown(f"### ⚙️ {model_name} Parameters")
            model_parameters[model_name] = configure_parameters(model_config, model_name)

    return prompt, model_parameters, selected_model_names


async def main() -> None:
    """Main application logic."""
    initialize_page()

    col1, col2 = st.columns([2, 1])
    db_manager = DatabaseManager()

    with col1:
        prompt, model_parameters, selected_model_names = render_model_selection()

        if st.button("🚀 Generate Images"):
            if not prompt:
                st.error("🚫 Please enter a prompt.")
                return

            with st.spinner("🎨 Creating your masterpiece..."):
                generation_tasks = [
                    generate_images(model_name, prompt, model_parameters.get(model_name, {}), db_manager)
                    for model_name in selected_model_names
                ]
                await asyncio.gather(*generation_tasks)

    with col2:
        st.markdown("### 📜 Generation History")
        display_history(db_manager)


if __name__ == "__main__":
    asyncio.run(main())

"""
AI Image Generator Web Application

Description:
    A Streamlit web application for generating images using various AI models.  Supports multiple
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

import streamlit as st
import asyncio
from dotenv import load_dotenv
from config.models import ModelRegistry
from database.manager import DatabaseManager
from ui.components import configure_parameters, display_history
from generators.factory import create_generator
import logging

logging.basicConfig(
    level=logging.WARNING,  # Default level for all loggers
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Set specific level for mongo_utils logger
logging.getLogger("generators").setLevel(logging.DEBUG)

load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def main():
    # Title with emoji and subtitle
    st.title("🎨 AI Image Generator")
    st.markdown("*Transform your ideas into stunning images using AI*")

    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])

    with col1:
        db_manager = DatabaseManager()
        available_models = ModelRegistry.get_all_models()

        selected_model_names = st.multiselect(
            "🤖 Select AI Models",
            options=[model.name for model in available_models],
            default=available_models[0].name if available_models else None,
        )

        st.markdown("### ✍️ Enter your prompt")
        prompt = st.text_area("Be descriptive for better results!", height=100)

        model_parameters = {}
        for model_name in selected_model_names:
            model_config = ModelRegistry.get_model(model_name)
            if model_config:
                st.markdown(f"### ⚙️ {model_name} Parameters")
                model_parameters[model_name] = configure_parameters(
                    model_config, model_name
                )

        if st.button("🚀 Generate Images"):
            if not prompt:
                st.error("🚫 Please enter a prompt.")
                return

            with st.spinner("🎨 Creating your masterpiece..."):
                for model_name in selected_model_names:
                    model_config = ModelRegistry.get_model(model_name)
                    if model_config:
                        generator = create_generator(model_config)
                        parameters = model_parameters.get(model_name, {})
                        if generator.validate_parameters(parameters):
                            result = await generator.generate(prompt, parameters)

                            if result.success:
                                st.success(
                                    f"✨ Image generated successfully with {model_name}!"
                                )

                                # Create columns for images
                                image_cols = st.columns(len(result.images))
                                for idx, image in enumerate(result.images):
                                    db_manager.save_generation(
                                        model_name, prompt, parameters, image
                                    )
                                    with image_cols[idx]:
                                        # Display thumbnail that expands on click
                                        st.image(
                                            image,
                                            use_container_width=True,
                                            caption=f"Image {idx + 1}",
                                        )
                                        # Add download button for each image
                                        st.download_button(
                                            label="📥 Download",
                                            data=image,
                                            file_name=f"generated_image_{model_name}_{idx + 1}.png",
                                            mime="image/png",
                                        )
                            else:
                                st.error(
                                    f"❌ Image generation failed for {model_name}: {result.error_message}"
                                )
                        else:
                            st.error(f"⚠️ Invalid parameters for {model_name}")

    with col2:
        st.markdown("### 📜 Generation History")
        display_history(db_manager)


if __name__ == "__main__":
    asyncio.run(main())

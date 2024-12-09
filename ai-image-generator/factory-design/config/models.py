"""
Models configuration for various AI image generation services.

This module defines the data models and configurations for different AI image generation
services, including Stability AI, FLUX, DALL-E, and FluxSchnell.  It leverages common
parameter configurations for better maintainability and reduces code duplication.
"""

from typing import Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, field_validator


class WidgetType(str, Enum):
    TEXT_AREA = "text_area"
    SLIDER = "slider"
    SLIDER_INT = "slider_int"
    SELECTBOX = "selectbox"
    NUMBER_INPUT = "number_input"
    CHECKBOX = "checkbox"
    TEXT_INPUT = "text_input"


class ModelType(str, Enum):
    STABILITY = "stability"
    FLUXPro = "fluxpro"
    DALLE = "dalle"
    FLUX = "flux"


class ParameterConfig(BaseModel):
    type: WidgetType
    label: str
    default: Optional[Union[str, int, float, bool]] = None
    help: str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    step: Optional[Union[int, float]] = None
    options: Optional[List[str]] = None

    @field_validator("default")
    def validate_default(cls, v, info):
        if info.data["type"] == WidgetType.SELECTBOX:
            if not info.data.get("options"):
                return v
            if v not in info.data.get("options", []):
                raise ValueError("Default value must be in options")
        return v


class ModelConfig(BaseModel):
    name: str
    description: Optional[str] = None
    endpoint: HttpUrl
    api_key_env: str
    model_type: ModelType
    parameters: dict[str, ParameterConfig]

    @field_validator("parameters")
    def validate_parameters(cls, v):
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v


# Common parameter configurations shared across models
COMMON_PARAMETERS = {
    "width_height": {
        "width": ParameterConfig(
            type=WidgetType.SLIDER_INT,
            label="Width",
            default=512,
            min_value=128,
            max_value=2048,
            help="Image width in pixels",
        ),
        "height": ParameterConfig(
            type=WidgetType.SLIDER_INT,
            label="Height",
            default=512,
            min_value=128,
            max_value=2048,
            help="Image height in pixels",
        ),
    },
    "seed": {
        "seed": ParameterConfig(
            type=WidgetType.NUMBER_INPUT,
            label="Seed",
            default=0,
            min_value=0,
            max_value=9007199254740991,  # Max safe integer in JavaScript
            help="Random seed (0 means random)",
        )
    },
    "webhook": {
        "webhook": ParameterConfig(
            type=WidgetType.TEXT_INPUT,
            label="Webhook URL",
            default=None,
            help="Webhook to call when inference is done",
        )
    },
    "num_images": {
        "num_images": ParameterConfig(
            type=WidgetType.SLIDER_INT,
            label="Number of Images",
            default=1,
            min_value=1,
            max_value=4,
            help="Number of images to generate",
        )
    },
    "num_inference_steps": {
        "num_inference_steps": ParameterConfig(
            type=WidgetType.SLIDER_INT,
            label="Inference Steps",
            default=50,
            min_value=1,
            max_value=50,
            help="Number of denoising steps",
        )
    },
    "cfg_scale": {
        "cfg_scale": ParameterConfig(
            type=WidgetType.SLIDER,
            label="CFG Scale",
            default=7.0,
            min_value=1.0,
            max_value=20.0,
            help="Classifier-free guidance scale",
        )
    },
    "negative_prompt": {
        "negative_prompt": ParameterConfig(
            type=WidgetType.TEXT_AREA,
            label="Negative Prompt",
            default="",
            help="Negative text prompt",
        )
    },
    "prompt_upsampling": {
        "prompt_upsampling": ParameterConfig(
            type=WidgetType.CHECKBOX,
            label="Prompt Upsampling",
            default=False,
            help="Automatically modifies the prompt for more creative generation",
        )
    },
    "safety_tolerance": {
        "safety_tolerance": ParameterConfig(
            type=WidgetType.SLIDER,
            label="Safety Tolerance",
            default=2.0,
            min_value=0.0,
            max_value=6.0,
            help="Tolerance level for moderation (0: strict, 6: least strict)",
        )
    },
}


class ModelRegistry:
    _models: dict[str, ModelConfig] = {}

    @classmethod
    def register(cls, model_config: ModelConfig) -> None:
        cls._models[model_config.name] = model_config

    @classmethod
    def get_model(cls, name: str) -> Optional[ModelConfig]:
        return cls._models.get(name)

    @classmethod
    def get_all_models(cls) -> List[ModelConfig]:
        return list(cls._models.values())


# Register models
ModelRegistry.register(
    ModelConfig(
        name="StabilityD 3.5",
        description="Stability AI Stable Diffusion 3.5",
        endpoint="https://api.deepinfra.com/v1/inference/stabilityai/sd3.5",
        api_key_env="DEEPINFRA_API_KEY",
        model_type=ModelType.STABILITY,
        parameters={
            **COMMON_PARAMETERS["negative_prompt"],
            **COMMON_PARAMETERS["num_images"],
            **COMMON_PARAMETERS["num_inference_steps"],
            **COMMON_PARAMETERS["width_height"],
            **COMMON_PARAMETERS["cfg_scale"],
            **COMMON_PARAMETERS["seed"],
            # **COMMON_PARAMETERS["webhook"],
        },
    )
)
ModelRegistry.register(
    ModelConfig(
        name="StabilityD 3.5 Medium",
        description="Stability AI Stable Diffusion 3.5",
        endpoint="https://api.deepinfra.com/v1/inference/stabilityai/sd3.5-medium",
        api_key_env="DEEPINFRA_API_KEY",
        model_type=ModelType.STABILITY,
        parameters={
            **COMMON_PARAMETERS["negative_prompt"],
            **COMMON_PARAMETERS["num_images"],
            **COMMON_PARAMETERS["num_inference_steps"],
            **COMMON_PARAMETERS["width_height"],
            **COMMON_PARAMETERS["cfg_scale"],
            **COMMON_PARAMETERS["seed"],
            # **COMMON_PARAMETERS["webhook"],
        },
    )
)

ModelRegistry.register(
    ModelConfig(
        name="Flux-Schnell",
        description="FluxSchnell",
        endpoint="https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-schnell",
        api_key_env="DEEPINFRA_API_KEY",
        model_type=ModelType.FLUX,
        parameters={
            **COMMON_PARAMETERS["num_images"],
            **COMMON_PARAMETERS["num_inference_steps"],
            **{
                k: ParameterConfig(**{**v.dict(), "default": 256})
                for k, v in COMMON_PARAMETERS["width_height"].items()
            },
            **COMMON_PARAMETERS["seed"],
            # **COMMON_PARAMETERS["webhook"],
        },
    )
)

ModelRegistry.register(
    ModelConfig(
        name="FLUX-pro",
        description="Black Forest Labs FLUX-pro",
        endpoint="https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-pro",
        api_key_env="DEEPINFRA_API_KEY",
        model_type=ModelType.FLUX,
        parameters={
            **{
                k: ParameterConfig(
                    **{
                        **v.dict(),
                        "step": 32,
                        "min_value": 256,
                        "max_value": 1440,
                    }
                )
                for k, v in COMMON_PARAMETERS["width_height"].items()
            },
            **COMMON_PARAMETERS["prompt_upsampling"],
            **COMMON_PARAMETERS["safety_tolerance"],
            **COMMON_PARAMETERS["seed"],
            # **COMMON_PARAMETERS["webhook"],
        },
    )
)
ModelRegistry.register(
    ModelConfig(
        name="FLUX-1-dev",
        description="Black Forest Labs FLUX-1-dev",
        endpoint="https://api.deepinfra.com/v1/inference/black-forest-labs/FLUX-1-dev",
        api_key_env="DEEPINFRA_API_KEY",
        model_type=ModelType.FLUX,
        parameters={
            **COMMON_PARAMETERS["width_height"],
            **{
                k: ParameterConfig(**{**v.dict(), "default": 25})
                for k, v in COMMON_PARAMETERS["num_inference_steps"].items()
            },
            # **COMMON_PARAMETERS["safety_tolerance"],
            **COMMON_PARAMETERS["seed"],
            # **COMMON_PARAMETERS["webhook"],
        },
    )
)


ModelRegistry.register(
    ModelConfig(
        name="StabilityAI",
        description="Stability AI Stable Diffusion 3.5",
        endpoint="https://api.stability.ai/v2beta/stable-image/generate/sd3",
        api_key_env="STABILITYAI_API_KEY",
        model_type=ModelType.STABILITY,
        parameters={
            **COMMON_PARAMETERS["negative_prompt"],
            **COMMON_PARAMETERS["num_images"],
            **COMMON_PARAMETERS["width_height"],
            **COMMON_PARAMETERS["cfg_scale"],
            **COMMON_PARAMETERS["seed"],
            "model": ParameterConfig(
                type=WidgetType.SELECTBOX,
                label="Model Version",
                default="sd3.5-large",
                options=["sd3.5-large", "sd3.5-large-turbo", "sd3.5-medium"],
                help="Select the model version to use",
            ),
        },
    )
)


ModelRegistry.register(
    ModelConfig(
        name="DALL-E",
        description="OpenAI DALL-E",
        endpoint="https://api.openai.com/v1/images/generations",
        api_key_env="OPENAI_API_KEY",
        model_type=ModelType.DALLE,
        parameters={
            # "n": ParameterConfig(
            #     type=WidgetType.SLIDER_INT,
            #     label="Number of Images",
            #     default=1,
            #     min_value=1,
            #     max_value=10,
            #     help="Number of images to generate",
            # ),
            "size": ParameterConfig(
                type=WidgetType.SELECTBOX,
                label="Image Size",
                default="1024x1024",
                options=["1024x1024", "1024x1792", "1792x1024"],
                help="Size of the generated images",
            ),
            "quality": ParameterConfig(
                type=WidgetType.SELECTBOX,
                label="Quality",
                default="standard",
                options=["standard", "hd"],
                help="Quality of the generated images",
            ),
            "model": ParameterConfig(
                type=WidgetType.SELECTBOX,
                label="Model",
                default="dall-e-3",
                options=["dall-e-3", "dall-e-2"],
                help="DALL-E model version",
            ),
        },
    )
)

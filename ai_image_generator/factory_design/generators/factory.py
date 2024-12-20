from generators.base import BaseGenerator
from generators.stability import StabilityGenerator
from generators.fluxpro import FluxProGenerator
from generators.dalle import DalleGenerator
from generators.flux import FluxGenerator
from config.models import ModelConfig, ModelType


def create_generator(model_config: ModelConfig) -> BaseGenerator:
    """
    Creates and returns an appropriate image generator based on the provided model configuration.

    Args:
        model_config (ModelConfig): Configuration object containing model type and settings

    Returns:
        BaseGenerator: An instance of the appropriate generator class for the specified model type

    Raises:
        ValueError: If the model type specified in the configuration is not recognized
    """
    if model_config.model_type == ModelType.STABILITY:
        return StabilityGenerator(model_config)
    elif model_config.model_type == ModelType.FLUXPro:
        return FluxProGenerator(model_config)
    elif model_config.model_type == ModelType.DALLE:
        return DalleGenerator(model_config)
    elif model_config.model_type == ModelType.FLUX:
        return FluxGenerator(model_config)
    else:
        raise ValueError(f"Unknown model type: {model_config.model_type}")

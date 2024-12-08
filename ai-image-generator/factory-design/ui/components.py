import streamlit as st
from config.models import ModelConfig, WidgetType


def configure_parameters(model_config: ModelConfig, key_prefix: str) -> dict:
    parameters = {}
    with st.expander(f"{model_config.name} Parameters", expanded=True):
        for param_name, param_config in model_config.parameters.items():
            widget_key = f"{key_prefix}_{param_name}"
            if param_config.type == WidgetType.TEXT_AREA:
                parameters[param_name] = st.text_area(
                    param_config.label,
                    value=param_config.default,
                    help=param_config.help,
                    key=widget_key,
                )
            elif param_config.type in (WidgetType.SLIDER, WidgetType.SLIDER_INT):
                parameters[param_name] = st.slider(
                    param_config.label,
                    min_value=param_config.min_value,
                    max_value=param_config.max_value,
                    value=param_config.default,
                    step=param_config.step,
                    help=param_config.help,
                    key=widget_key,
                )
            elif param_config.type == WidgetType.SELECTBOX:
                parameters[param_name] = st.selectbox(
                    param_config.label,
                    options=param_config.options,
                    index=param_config.options.index(param_config.default),
                    help=param_config.help,
                    key=widget_key,
                )
            elif param_config.type == WidgetType.NUMBER_INPUT:
                parameters[param_name] = st.number_input(
                    param_config.label,
                    value=param_config.default,
                    min_value=param_config.min_value,
                    max_value=param_config.max_value,
                    help=param_config.help,
                    key=widget_key,
                )
            elif param_config.type == WidgetType.CHECKBOX:
                parameters[param_name] = st.checkbox(
                    param_config.label,
                    value=param_config.default,
                    help=param_config.help,
                    key=widget_key,
                )
            elif param_config.type == WidgetType.TEXT_INPUT:
                parameters[param_name] = st.text_input(
                    param_config.label,
                    value=param_config.default,
                    help=param_config.help,
                    key=widget_key,
                )

    return parameters


def display_history(db_manager):
    with st.expander("Generation History"):
        history = db_manager.get_history()
        for record in history:
            st.write(f"**Model:** {record[2]}")
            st.write(f"**Prompt:** {record[3]}")
            st.write(f"**Parameters:** {record[4]}")
            st.image(record[5])
            st.divider()

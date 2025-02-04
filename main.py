"""
Alert Configuration Generator Web App

This Streamlit application provides a user interface for converting natural language
descriptions into structured alert configurations for camera systems. It communicates
with a FastAPI backend service that processes the natural language input using OpenAI's
GPT model.

The application supports three types of alerts:
1. ObjectCountAlert - For counting objects (e.g., people, cars)
2. TimerAlert - For duration-based events
3. ZoneAlert - For detecting objects in specific zones

Dependencies:
    - streamlit: For creating the web interface
    - requests: For making HTTP requests to the API
    - json: For formatting JSON data
    - typing: For type hints

Author: Jake Hulme
Date: February 2025
"""

import streamlit as st
import requests
import json
import os
from typing import Optional

# Default API configuration
DEFAULT_API_HOST = "http://34.67.4.17:8080"
DEFAULT_API_PATH = "/api/v1/chat"


def get_api_url() -> str:
    """
    Get the API URL from environment variable or Streamlit config.

    Returns:
        str: The complete API URL
    """
    # Try to get from environment variable first
    api_url = os.getenv("ALERT_API_URL")

    # If not in environment, check streamlit state
    if not api_url:
        if 'api_url' not in st.session_state:
            st.session_state.api_url = f"{DEFAULT_API_HOST}{DEFAULT_API_PATH}"
        api_url = st.session_state.api_url

    return api_url


def send_alert_request(message: str, api_url: Optional[str] = None) -> Optional[dict]:
    """
    Sends a natural language message to the API and receives an alert configuration.

    Args:
        message (str): The natural language description of the desired alert
        api_url (Optional[str]): Override URL for the alert configuration API

    Returns:
        Optional[dict]: The API response containing the alert configuration,
                       or None if an error occurs
    """
    try:
        # Use provided URL or get from configuration
        url = api_url or get_api_url()

        payload = {
            "user_id": "streamlit_user",
            "message": message,
            "camera_id": None
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with API: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def format_json(json_data: dict) -> str:
    """Format JSON data with proper indentation for display."""
    return json.dumps(json_data, indent=2)


def main():
    """Main application function that sets up the Streamlit interface."""
    st.title("Alert Configuration Generator")
    st.write("Convert natural language into alert configurations")

    # Add API configuration in sidebar
    with st.sidebar:
        st.header("API Configuration")
        api_host = st.text_input(
            "API Host",
            value=DEFAULT_API_HOST,
            help="The base URL of the API server"
        )
        api_path = st.text_input(
            "API Path",
            value=DEFAULT_API_PATH,
            help="The endpoint path for alert configuration"
        )
        st.session_state.api_url = f"{api_host}{api_path}"

        st.write("Full API URL:", st.session_state.api_url)

        if st.button("Test Connection"):
            try:
                response = requests.get(api_host)
                if response.ok:
                    st.success("Successfully connected to API server!")
                else:
                    st.error(f"Failed to connect: {response.status_code}")
            except requests.exceptions.RequestException:
                st.error("Could not connect to API server")

    # Example messages
    with st.expander("See example messages"):
        st.markdown("""
        Try these example messages:
        - Alert me when there are more than 10 people in the garden
        - If a car stays in the driveway for more than 5 minutes, send an alert
        - Notify me if someone enters zone A and then moves to zone B
        """)

    # User input section
    message = st.text_area(
        "Enter your alert message:",
        height=100,
        help="Describe the alert condition in natural language (see example messages)"
    )

    if st.button("Generate Alert Configuration"):
        if not message.strip():
            st.warning("Please enter a message")
        else:
            with st.spinner("Processing..."):
                result = send_alert_request(message)

                if result and result.get("status") == "success":
                    st.success("Alert configuration generated successfully!")

                    st.subheader("Generated Alert Configuration:")
                    st.code(format_json(result["alert_config"]), language="json")

                    st.subheader("Alert Explanation:")
                    alert_type = result["alert_config"]["type"]
                    params = result["alert_config"]["params"]

                    if alert_type == "ObjectCountAlert":
                        st.write(
                            f"This alert will trigger when the count of "
                            f"'{params['class_name']}' is {params['comparison']} "
                            f"{params['count_value']}"
                        )

                    elif alert_type == "TimerAlert":
                        st.write(
                            f"This alert will trigger after {params['duration']} "
                            "seconds"
                        )

                    elif alert_type == "ZoneAlert":
                        st.write(
                            f"This alert will trigger when a "
                            f"{params['target_object']} is detected in the "
                            "specified zone"
                        )


if __name__ == "__main__":
    st.set_page_config(
        page_title="Alert Configuration Generator",
        page_icon="🎥",
        layout="wide"
    )
    main()

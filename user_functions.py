import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
import requests
from config import DefaultConfig as config
from typing import Any, Callable, Set, Dict, List, Optional
import json


def create_delivery_order(order_id: str, destination: str) -> str:
    """
    creates a consignment delivery order (i.e. a shipment order) for the given order_id and destination location

    :param order_id (str): The order number of the purchase made by the user.
    :param destination (str): The location where the order is to be delivered.
    :return: generated delivery order number.
    :rtype: Any
    """

    api_url = config.az_logic_app_url
    print("making the Logic app call.................")
    # make a HTTP POST API call with json payload
    response = requests.post(
        api_url,
        json={"order_id": order_id, "destination": destination},
        headers={"Content-Type": "application/json"},
    )

    print("response from logic app", response.text)
    return json.dumps(response.text)

    # Statically defined user functions for fast reference

def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.

    :param location (str): The location to fetch weather for.
    :return: Weather information as a JSON string.
    :rtype: str
    """
    # In a real-world scenario, you'd integrate with a weather API.
    # Here, we'll mock the response.
    print("fetching weather for location: ", location)
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}
    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    weather_json = json.dumps({"weather": weather})
    return weather_json

user_functions= [create_delivery_order,fetch_weather]

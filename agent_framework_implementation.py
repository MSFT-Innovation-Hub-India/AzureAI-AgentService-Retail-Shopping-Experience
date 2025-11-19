"""
Microsoft Agent Framework implementation for Contoso Retail Fashion Agent.
This module demonstrates the usage of the new Microsoft Agent Framework
for building a retail shopping assistant with OpenAPI integration and function calling.
"""

import asyncio
import os
from typing import Optional, Annotated
from agent_framework import ChatAgent
from agent_framework.azure_ai import AzureAIChatClient
from azure.identity import DefaultAzureCredential
from config import DefaultConfig as config
from pydantic import Field
import json
import requests

def search_products_by_category(
    category: Annotated[str, Field(description="The product category to search for, e.g., 'winter wear', 'summer wear', 'accessories'")]
) -> str:
    """
    Search for products by category in the Contoso Retail Fashion catalog.
    Returns a list of available products in the specified category.
    """
    try:
        api_url = f"https://contosoretailfashions.azurewebsites.net/SearchProductsByCategory"
        response = requests.get(api_url, params={"category": category}, timeout=10)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to search products: {str(e)}"})


def search_products_by_category_and_price(
    category: Annotated[str, Field(description="The product category to search for")],
    max_price: Annotated[float, Field(description="Maximum price for the products")]
) -> str:
    """
    Search for products by category and filter by maximum price.
    Returns products within the specified price range.
    """
    try:
        api_url = f"https://contosoretailfashions.azurewebsites.net/SearchProductsByCategoryAndPrice"
        response = requests.get(
            api_url, 
            params={"category": category, "maxPrice": max_price},
            timeout=10
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to search products by price: {str(e)}"})


def order_product(
    product_id: Annotated[int, Field(description="The ID of the product to order")],
    quantity: Annotated[int, Field(description="The quantity to order")]
) -> str:
    """
    Place an order for a product with the specified quantity.
    Returns order confirmation details.
    """
    try:
        api_url = f"https://contosoretailfashions.azurewebsites.net/OrderProduct"
        response = requests.post(
            api_url,
            params={"id": product_id, "quantity": quantity},
            timeout=10
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to order product: {str(e)}"})


def create_delivery_order(
    order_id: Annotated[str, Field(description="The order number/ID for the purchase made by the customer")],
    destination: Annotated[str, Field(description="The delivery address/location where the order should be shipped")]
) -> str:
    """
    Create a consignment delivery order (shipment) for a placed order.
    This creates a shipment record for delivering the order to the customer's address.
    """
    try:
        api_url = config().az_logic_app_url
        if not api_url:
            return json.dumps({"error": "Logic App URL not configured"})
        
        response = requests.post(
            api_url,
            json={"order_id": order_id, "destination": destination},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return json.dumps({"status": "success", "details": response.text})
    except Exception as e:
        return json.dumps({"error": f"Failed to create delivery order: {str(e)}"})


class ContosoRetailAgent:
    """
    A retail shopping assistant agent built using Microsoft Agent Framework.
    This agent integrates with Azure OpenAI and provides shopping assistance
    with OpenAPI integration and function calling for product operations.
    """
    
    def __init__(self):
        """Initialize the Contoso Retail Agent with Azure AI client."""
        self.config = config()
        self.credential = DefaultAzureCredential()
        
        # Parse connection string to extract endpoint and other details
        # Format: "endpoint;subscription_id;resource_group;project_name"
        conn_parts = self.config.az_agentic_ai_service_connection_string.split(';')
        self.endpoint = f"https://{conn_parts[0]}" if not conn_parts[0].startswith('https://') else conn_parts[0]
        
        # Create Azure AI chat client for the agent
        self.chat_client = AzureAIChatClient(
            endpoint=self.endpoint,
            credential=self.credential,
            model="gpt-4o-mini"
        )
        
        # Define agent instructions
        self.instructions = """You are an AI Assistant for Contoso Retail Fashion, designed to help customers with their shopping needs.
        
Your capabilities include:
1. Searching for products by category (e.g., winter wear, summer wear, accessories)
2. Searching for products by category and price range
3. Helping customers place orders for products
4. Creating delivery/shipment orders for purchased items

Always be helpful, friendly, and guide customers through their shopping experience.
When customers ask about products, use the available functions to search and retrieve accurate information.
When customers want to order products, collect necessary details and process their orders efficiently."""

        # Define the tools (functions) available to the agent
        self.tools = [
            search_products_by_category,
            search_products_by_category_and_price,
            order_product,
            create_delivery_order
        ]

        self.agent: Optional[ChatAgent] = None

    async def create_agent(self) -> ChatAgent:
        """
        Create and configure the retail agent with Microsoft Agent Framework.
        Includes function calling tools for product search, ordering, and delivery.
        
        Returns:
            ChatAgent: Configured chat agent instance with attached tools
        """
        # Create the agent with the chat client, instructions, and tools
        self.agent = ChatAgent(
            chat_client=self.chat_client,
            instructions=self.instructions,
            name="contoso-retail-fashions-assistant",
            tools=self.tools  # Attach function calling tools
        )
        
        print(f"✓ Created Contoso Retail Fashion Agent using Microsoft Agent Framework")
        print(f"✓ Attached {len(self.tools)} function tools for product operations")
        return self.agent
    
    async def run_agent(self, user_message: str) -> str:
        """
        Run the agent with a user message and return the response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            str: The agent's response
        """
        if not self.agent:
            await self.create_agent()
        
        # Run the agent with the user's message
        result = await self.agent.run(user_message)
        return result

    async def run_conversation(self):
        """
        Run an interactive conversation loop with the agent.
        Useful for testing and demonstration purposes.
        """
        if not self.agent:
            await self.create_agent()
        
        print("\n" + "="*60)
        print("Contoso Retail Fashion Shopping Assistant")
        print("Powered by Microsoft Agent Framework")
        print("="*60 + "\n")
        print("Type 'exit' or 'quit' to end the conversation.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nThank you for shopping with Contoso Retail Fashion!")
                    break
                
                if not user_input:
                    continue
                
                # Get agent response
                response = await self.run_agent(user_input)
                print(f"\nAssistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


async def main():
    """Main function to create and test the agent."""
    try:
        # Create the Contoso Retail Agent
        retail_agent = ContosoRetailAgent()
        
        # Create the agent
        agent = await retail_agent.create_agent()
        print(f"Agent created successfully: {agent.name}")
        
        # Optionally run a test conversation
        # Uncomment the following line to run an interactive conversation
        # await retail_agent.run_conversation()
        
        # Or test with a single message
        test_message = "Hi, I'm looking for winter wear. What do you have available?"
        print(f"\nTest Query: {test_message}")
        response = await retail_agent.run_agent(test_message)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        raise


if __name__ == "__main__":
    print("Initializing Contoso Retail Fashion Agent...")
    print("Using Microsoft Agent Framework\n")
    asyncio.run(main())

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import (
    OpenApiTool,
    OpenApiAnonymousAuthDetails,
)
import jsonref
from azure.ai.projects.models import FunctionTool, ToolSet
from user_functions import user_functions
from config import DefaultConfig as config

functions = FunctionTool(functions=user_functions)

def create_agent():

        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=config.az_agentic_ai_service_connection_string,
        )
        
        # read the swagger file for the Contoso Retail Fashion API definition
        with open("./data-files/swagger.json", "r") as f:
            openapi_spec = jsonref.loads(f.read())
        auth = OpenApiAnonymousAuthDetails()

        # Initialize agent OpenApi tool using the read in OpenAPI spec
        api_tool = OpenApiTool(
            name="contoso_retail_fashion_api",
            spec=openapi_spec,
            description="help users order a product based on id and quantity, search products by category, and search for products based on their category and price.",
            auth=auth,
        )

        # Initialize agent toolset with user functions
        toolset = ToolSet()
        toolset.add(functions)
        toolset.add(api_tool)

        # print("toolsets definition", toolset.definitions)

        agent = project_client.agents.create_agent(
            model="gpt-4o-mini",
            name="contoso-retail-fashions-ai-agent",
            instructions="You are an AI Assistant tasked with helping the customers of Contoso retail fashions with their shopping requirements. You have access to the APIs in contoso_retail_fashion_api that you need to call to respond to the user queriest",
            tools=toolset.definitions,
        )

        print(f"created agent with id {agent.id}")
        

def main():
    # Create an agent
    create_agent()
    
if __name__ == "__main__":
    main()
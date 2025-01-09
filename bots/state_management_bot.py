from botbuilder.core import ActivityHandler, ConversationState, TurnContext, UserState

from data_models.user_profile import UserProfile
from data_models.conversation_data import ConversationData
import time
from datetime import datetime
from config import DefaultConfig
from azure.ai.projects.models import (
    FunctionTool,
    RequiredFunctionToolCall,
    SubmitToolOutputsAction,
    ToolOutput,
)

import time
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import (
    OpenApiTool,
    OpenApiAnonymousAuthDetails,
)
import jsonref

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import FunctionTool, ToolSet
from user_functions import user_functions

functions = FunctionTool(functions=user_functions)
        
class StateManagementBot(ActivityHandler):

    connection = None
    # assistant_id = "asst_FguPQz5y5prwRADEepQkwope"

    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.config = DefaultConfig()

        # Create Azure OpenAI client
        self.project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=self.config.az_agentic_ai_service_connection_string,
        )

        
        # retrieve the agent already created
        self.agent = self.project_client.agents.get_agent(DefaultConfig.az_assistant_id)
        print("retrieved agent with id ", self.agent.id)

        self.conversation_data_accessor = self.conversation_state.create_property(
            "ConversationData"
        )
        self.user_profile_accessor = self.user_state.create_property("UserProfile")

    async def on_message_activity(self, turn_context: TurnContext):

        # Get the state properties from the turn context.
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(
            turn_context, ConversationData
        )

        if user_profile.name is None:
            # First time around this is undefined, so we will prompt user for name.
            if conversation_data.prompted_for_user_name:
                # Set the name to what the user provided.
                user_profile.name = turn_context.activity.text

                # Acknowledge that we got their name.
                await turn_context.send_activity(
                    f"Thanks { user_profile.name }. Let me know how can I help you today"
                )

                # Reset the flag to allow the bot to go though the cycle again.
                conversation_data.prompted_for_user_name = False
            else:
                # Prompt the user for their name.
                await turn_context.send_activity(
                    "I am your AI Assistant from Contoso Fashion Retail. I can help you shop for your favorite fashion items. "
                    + "Can you help me with your name?"
                )

                # Set the flag to true, so we don't prompt in the next turn.
                conversation_data.prompted_for_user_name = True
        else:
            # Add message details to the conversation data.
            conversation_data.timestamp = self.__datetime_from_utc_to_local(
                turn_context.activity.timestamp
            )
            conversation_data.channel_id = turn_context.activity.channel_id

            l_thread = conversation_data.thread

            if l_thread is None:
                # Create a thread
                conversation_data.thread = self.project_client.agents.create_thread()
                l_thread = conversation_data.thread
                # Threads have an id as well
                print("creating a new session and thread for this user!")
                print("Created thread bearing Thread id: ", conversation_data.thread.id)

            # Create message to thread
            message = self.project_client.agents.create_message(
                thread_id=l_thread.id, role="user", content=turn_context.activity.text
            )
            print(f"Created message, ID: {message.id}")

            # [
            #     print(json.dumps(tool.as_dict(), indent=4))
            #     for tool in self.agent.tools
            #     if tool.type == "function"
            # ]

            run = self.project_client.agents.create_run(
                thread_id=l_thread.id, assistant_id=self.agent.id
            )
            print(f"Created thread run, ID: {run.id}")

            while run.status in ["queued", "in_progress", "requires_action"]:
                time.sleep(1)
                run = self.project_client.agents.get_run(
                    thread_id=l_thread.id, run_id=run.id
                )

                if run.status == "requires_action" and isinstance(
                    run.required_action, SubmitToolOutputsAction
                ):
                    print("Run requires function call to be done..")
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    if not tool_calls:
                        print("No tool calls provided - cancelling run")
                        self.project_client.agents.cancel_run(
                            thread_id=l_thread.id, run_id=run.id
                        )
                        break

                    tool_outputs = []
                    for tool_call in tool_calls:
                        if isinstance(tool_call, RequiredFunctionToolCall):
                            try:
                                print(f"Executing tool call: {tool_call}")
                                output = functions.execute(tool_call)
                                tool_outputs.append(
                                    ToolOutput(
                                        tool_call_id=tool_call.id,
                                        output=output,
                                    )
                                )
                            except Exception as e:
                                print(f"Error executing tool_call {tool_call.id}: {e}")

                    print(f"Tool outputs: {tool_outputs}")
                    if tool_outputs:
                        self.project_client.agents.submit_tool_outputs_to_run(
                            thread_id=l_thread.id,
                            run_id=run.id,
                            tool_outputs=tool_outputs,
                        )

                    print(f"Current run status: {run.status}")

            # Fetch and log all messages
            messages = self.project_client.agents.list_messages(thread_id=l_thread.id)
            # print(f"Messages: {messages}")
            assistant_response = ""
            for message in messages["data"]:
                if message["role"] == "assistant":
                    assistant_response = message["content"][0]["text"]["value"]
                    break

            return await turn_context.send_activity(assistant_response)

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    def __datetime_from_utc_to_local(self, utc_datetime):
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
            now_timestamp
        )
        result = utc_datetime + offset
        return result.strftime("%I:%M:%S %p, %A, %B %d of %Y")

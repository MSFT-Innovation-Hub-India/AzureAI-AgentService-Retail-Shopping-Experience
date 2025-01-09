from openai import AzureOpenAI

class ConversationData:
    def __init__(
        self,
        timestamp: str = None,
        channel_id: str = None,
        prompted_for_user_name: bool = False,
        thread = None
    ):
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.prompted_for_user_name = prompted_for_user_name
        self.thread = thread
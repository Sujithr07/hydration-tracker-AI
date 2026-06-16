import os
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage,SystemMessage,AIMessage

from dotenv import load_dotenv

load_dotenv()

llm = init_chat_model("google_genai:gemini-2.5-flash-lite")


class WaterIntakeAgent:
    def __init__(self):
        self.history= []

    def analyse_intake(self, intake_ml):
        prompt= f"""
        you are a hydration assistant, the user has consumed {intake_ml} ml of water today.
        provide a hydration status and suggest if they need to drink more water
        """
        
        response= llm.invoke([HumanMessage(content=prompt)])

        return response.content
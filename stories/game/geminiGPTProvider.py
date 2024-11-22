'''
Created on Nov 19, 2024

@author: don_bacon
'''

from game.gptProvider import GPTProvider
from game.gameConstants import GPTProviders, GPTProviderKeyName, CardType
import google.generativeai as genai
from google.ai.generativelanguage_v1.types.generative_service import GenerateContentResponse
from pydantic import BaseModel
import typing_extensions as typing
import os

class StorySnippet(typing.TypedDict):
    line_number: int
    title: str
    story_text: str

class Card(BaseModel):
    line:int
    content:str

class Cards(BaseModel):
    cards:list[Card]

class GeminiGPTProvider(GPTProvider):
    '''
    API interface to Google Gemini
    '''

    def __init__(self, genre:str, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        '''
        Constructor
        '''
        super().__init__(genre, provider, model_name, card_type, prompt_source, system_instructions_source, temperature, output_format, candidate_count)
        
        self._model = genai.GenerativeModel(model_name) if self._system_instructions is None else genai.GenerativeModel(model_name, system_instructions=self._system_instructions)
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        #self.configure_model(temperature, output_format)

    def configure_model(self, temp:float, output_format:str):
        """Configure the Gemini GPT model
        """
        # [START configure_model_parameters]
        if output_format == "text":
            self._generation_config = genai.types.GenerationConfig(candidate_count=self._candidate_count, temperature=temp )
        elif output_format == "json":
            self._generation_config = \
                genai.types.GenerationConfig(candidate_count=self._candidate_count, temperature=temp, response_mime_type="application/json", response_schema=list[StorySnippet] )
        else:
            print(f"{output_format} output format is not supported")
            self._generation_config = None
        # [END configure_model_parameters]
    
    def generate_content(self, prompt:str=None):
        if prompt is not None:
            self._prompt = prompt
        # response: GenerateContentResponse
        response = self.model.generate_content(self._prompt, generation_config=self._generation_config)
        self._content = response.text
    
    
'''
Created on Nov 21, 2024

@author: don_bacon
'''

from game.gptProvider import GPTProvider
from game.gameConstants import GPTProviders, GPTProviderKeyName, CardType
from openai import OpenAI
from pydantic import BaseModel
import typing_extensions as typing
import os

class OPenAIGPTProvider(GPTProvider):
    '''
    API interface to OpenAI ChatGPT
    '''


    def __init__(self, genre:str, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        '''
        Constructor
        '''
        super().__init__(genre, provider, model_name, card_type, prompt_source, system_instructions_source, temperature, output_format, candidate_count)
        
    def configure_model(self, temp:float, output_format:str):
        """ 
        """
        org_id = os.environ["OPENAI_ORG_ID"]
        project_id = os.environ["OPENAI_PROJECT_ID"]
        apikey = os.environ["OPENAI_API_KEY"]
        self._client = OpenAI()
    
    def generate_content(self, prompt:str):
        """
        """
        self._prompt = prompt
        if self.model_name.startswith("o1-") or self._system_instructions is None:    # o1-mini and o1-preview do not support system role
                completion = self._client.chat.completions.create( model=self._model_name, \
                    messages=[ {"role": "user", "content": self._prompt}  ]  )
        else:
            completion = self._client.chat.completions.create( model=self._model_name, \
                messages=[ \
                    {"role": "system", "content": "You are a film script writer, skilled at writing a script in the noir genre with creative flair."}, \
                    {"role": "user", "content": self._prompt} \
                ]  )
        
        self._content = completion.choices[0].message
    
        
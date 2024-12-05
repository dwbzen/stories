'''
Created on Nov 21, 2024

@author: don_bacon
'''

from game.gptProvider import GPTProvider
from game.gameConstants import GPTProviders, GPTProviderKeyName, CardType, GenreType
from openai import OpenAI
from pydantic import BaseModel, Field
import os

class Card(BaseModel):
    """StoryCard number, type and text
    """
    card_type:str = Field(default="Story")
    line:int = Field(...)
    content:str = Field(...)

class OPenAIGPTProvider(GPTProvider):
    '''
    API interface to OpenAI ChatGPT
    '''


    def __init__(self, genre:GenreType, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        '''
        Constructor
        '''
        super().__init__(genre, provider, model_name, card_type, prompt_source, system_instructions_source, temperature, output_format, candidate_count)
        
    def configure_model(self, temperature:float, output_format:str):
        """ 
            temperature - temperature controls the randomness of the output. 
                  Use higher values for more creative responses, and lower values for more deterministic responses. 
                  Values can range from [0.0, 2.0]. Default value is 1.0
            output_format - output format: "text" or "json". Default is "text"
        """
        org_id = os.environ["OPENAI_ORG_ID"]
        project_id = os.environ["OPENAI_PROJECT_ID"]
        apikey = os.environ[GPTProviderKeyName.OPENAI.value]
        self._client = OpenAI()
    
    def generate_content(self, prompt:str):
        """
        """
        self._prompt = prompt
        if self.model_name.startswith("o1-") or self._system_instructions is None:    # o1-mini and o1-preview do not support system role
                completion = self._client.chat.completions.create( model=self._model_name, \
                    messages=[ {"role": "user", "content": self._prompt}  ]  )
        elif self.system_instructions is not None:
            completion = self._client.chat.completions.create( model=self._model_name, \
                messages=[ \
                    {"role": "system", "content": self.system_instructions}, \
                    {"role": "user", "content": self._prompt} \
                ]  )
        
        self._content = completion.choices[0].message    # ChatCompletionMessage
    
    def _generate_text_content(self):
        if self.model_name.startswith("o1-") or self._system_instructions is None:    # o1-mini and o1-preview do not support system role
                completion = self._client.chat.completions.create( model=self._model_name, \
                    messages=[ {"role": "user", "content": self._prompt}  ]  )
        elif self.system_instructions is not None:
            completion = self._client.chat.completions.create( model=self._model_name, \
                messages=[ \
                    {"role": "system", "content": self.system_instructions}, \
                    {"role": "user", "content": self._prompt} \
                ]  )
        
        self._content = completion.choices[0].message    # ChatCompletionMessage
    
    def _generate_JSON_content(self):
        if self.model_name.startswith("o1-") or self._system_instructions is None:    # o1-mini and o1-preview do not support system role
                completion = self._client.beta.chat.completions.parse( model=self._model_name, \
                    messages=[ {"role": "user", "content": self._prompt}  ], \
                    response_format = Card )
                
        elif self.system_instructions is not None:
            completion = self._client.chat.completions.create( model=self._model_name, \
                messages=[ \
                    {"role": "system", "content": self.system_instructions}, \
                    {"role": "user", "content": self._prompt} ],
                response_format = Card  )
        
        self._content = completion.choices[0].message.parsed    # ChatCompletionMessage
        
        
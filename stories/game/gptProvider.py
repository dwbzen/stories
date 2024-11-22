'''
Created on Nov 19, 2024

@author: don_bacon
'''

from game.gameConstants import GPTProviders, GPTProviderKeyName, CardType
from game.environment import Environment
import os, sys
from abc import ABC, abstractmethod, ABCMeta

class GPTProvider(ABC):
    '''
    Abstract base class for providers (services) for GPT engines/APIs
    such as OpenAI's chat GPT and Google's Gemini.
    GPT stands for Generative Pre-trained Transformer, a type of 
    artificial intelligence (AI) model that uses deep learning to create human-like text.
    '''


    def __init__(self, genre:str, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        """
            Create and initialize a PromptManager.
            Arguments:
                genre - the genre of the story: 'horror' | 'noir' | 'romance'
                provider - the provider of the underlying API: GPTProvider.GEMINI or GPTProvider.OPENAI
                model_name - the name of the provider's model to use
                prompt_source - optional argument. If included, the name of the file containing the prompt. Default is None.
                                TODO - add MongoDB support
                temperature - temperature controls the randomness of the output. 
                              Use higher values for more creative responses, and lower values for more deterministic responses. 
                              Values can range from [0.0, 2.0]. Default value is 1.0
                output_format - output format: "text" or "JSON". Default is "text"
                candidate_count - specifies the number of generated responses to return. Currently, this value can only be set to 1.
                system_instructions_source - optional argument: the name of the file containing system instructions to the model. Default is None
                
            Note that the API keys must exist (i.e. exported) in the environment: GEMINI_API_KEY for Gemini, API_KEY for OpenAI.
            System and prompt files are assumed to be unstructured text. 
            They are also assumed to exist in the project resources/genres/<genre> folder, where <genre> :: 'horror' | 'noir' | 'romance'
            UNLESS a full path is provided.
        """
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        self._genre_folder = f"{self._resource_folder}/genres/{genre}"
        self._provider = provider
        self._model_name = model_name
        self._model = None
        
        self._prompt_source = prompt_source
        if prompt_source is not None:
            self._prompt_source = prompt_source if prompt_source.startswith("/") else f"{self._genre_folder}/{prompt_source}"
        self._set_prompt()
        
        self._system_instructions_source = system_instructions_source
        if system_instructions_source is not None:
            self._system_instructions_source = system_instructions_source if system_instructions_source.startswith("/") else f"{self._genre_folder}/{system_instructions_source}"
        self._set_system_instructions()
        
        self._candidate_count = candidate_count
        self._output_format = output_format
        self._content = None    # latest result of generate_content
        self._card_type = card_type
        # . 
        # Use higher values for more creative responses, and lower values for more deterministic responses. 
        # Values can range from [0.0, 2.0].
        self._temperature = temperature

        self._api_key_name = GPTProviderKeyName[self._provider.value.upper()]
        self._api_key = os.environ[self._api_key_name.value.upper()]
        self.configure_model(temperature, output_format)
    
    @abstractmethod
    def configure_model(self, temp:float, output_format:str):
        """Define in derived classes.
        """
        pass
    
    @abstractmethod
    def generate_content(self, prompt:str=None):
        """Define in derived classes.
        """
        pass
    
    @property
    def model(self):
        return self._model
    
    @property
    def model_name(self)->str:
        return self._model_name
    
    @property
    def card_type(self)->CardType:
        return self._card_type
    
    @card_type.setter
    def card_type(self, ct:CardType):
        self._card_type = ct
    
    @property
    def provider(self)->GPTProviders:
        return self._provider
    
    @property
    def prompt(self)->str:
        return self._prompt
    
    @prompt.setter
    def prompt(self, the_prompt):
        self._prompt = the_prompt
    
    @property
    def prompt_source(self)->str|None:
        """The name of the file containing the prompt.
            This can be a text (.txt) or image (.jpg, .png) file
        """
        return self.prompt_source
    
    @prompt_source.setter
    def prompt_source(self, source_filename):
        """Read the file identified by path and save as the prompt
            TODO support image files
        """
        self._prompt_source = source_filename
        
    
    def _set_prompt(self):
        if self._prompt_source is not None:
            with open(self._prompt_source, "r") as fp:
                self._prompt = fp.read()
            fp.close()
        else:
            self._prompt = None
            
    @property
    def system_instructions_source(self)->str|None:
        return self._system_instructions_source
    
    @system_instructions_source.setter
    def system_instructions_source(self, source_filename):
        """Read the file identified by filename and save as system_instructions
        """
        self._system_instructions_source = source_filename
        
    def _set_system_instructions(self):
        if self._system_instructions_source is not None:
            with open(self._system_instructions_source, "r") as fp:
                self._system_instructions = fp.read()
            fp.close()
        else:
            self._system_instructions = None
    
    @property
    def temperature(self)->float:
        return self._temperature
    
    @temperature.setter
    def temperature(self, temp:float):
        self._temperature = temp
        # reconfigure the model
        self.configure_model(temp, self._output_format)
    
    @property
    def output_format(self)->str:
        return self._output_format
    
    @output_format.setter
    def output_format(self, output_format:str):
        self.configure_model(self.temperature, output_format)
    
    @property
    def content(self)->str|None:
        return self._content


    

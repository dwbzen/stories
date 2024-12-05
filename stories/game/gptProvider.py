'''
Created on Nov 19, 2024

@author: don_bacon
'''

from game.gameConstants import GPTProviders, GPTProviderKeyName, CardType, GenreType
from game.environment import Environment
import os, sys
from abc import ABC, abstractmethod, ABCMeta

class GPTProvider(ABC):
    """
        Create a generative AI model and generate responses from text prompts.
        
        Sample text responses may include a title delimited by "**". For example:
        1. **The Attic:** The floorboards groaned under Don's weight as he crept towards the attic door. A low, guttural growl echoed from within, making his hair stand on end. "Cheryl, you sure you heard that?" he whispered, his voice cracking. "It's just the wind, Don," Cheryl replied, but her voice trembled. "Maybe we should just leave." 
        2. **The Mirror:** Beth stared into the antique mirror, her reflection warping and twisting as she touched the cold, tarnished surface. A chilling voice rasped from the depths of the mirror, "You're not supposed to be here." Her blood ran cold as the reflection blinked, a crimson eye gleaming in the darkness. 
        Sample responses that do not include a title:
        1.  The floorboards groaned under his weight as Don crept closer to the attic door. 
            "You hear that?" he whispered, his voice trembling. "It's coming from inside." 
            Cheryl gripped his arm, her face pale in the dim light. "Don't go in there," she pleaded, but the faint scratching sounds from within the attic were too much to ignore.
        2.  Beth shivered, pulling her thin jacket tighter around herself. 
            "This place is freezing," she muttered. Brian shrugged, fiddling with his phone. 
            "Maybe it's just the altitude. You know, high up in the mountains and all." 
            But the air in the cabin felt different, heavy and oppressive, like a cold hand was pressing down on their chests.
        The format of the responses  - for example numbering, including a title - can be controlled by the prompt itself,
        or through configuration for JSON output.
        
        Abstract base class for providers (services) for GPT engines/APIs
        such as OpenAI's chat GPT and Google's Gemini.
        GPT stands for Generative Pre-trained Transformer, a type of 
        artificial intelligence (AI) model that uses deep learning to create human-like text.
    """

    DEFAULT_PROMPT = "text:Write a haiku about recursion in programming."

    def __init__(self, genre:GenreType, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        """
            Create and initialize a GPTProvider.
            Arguments:
                genre - the genre of the story: 'horror' | 'noir' | 'romance'
                provider - the provider of the underlying API: GPTProvider.GEMINI or GPTProvider.OPENAI
                model_name - the name of the provider's model to use
                prompt_source - The name of the file containing the prompt, or the actual text to use as the prompt.
                    Formats are "file:<filename>" or "text:<text>". If prompt_source is None, it uses
                    the default_prompt value: "text:Write a haiku about recursion in programming."
                temperature - temperature controls the randomness of the output. 
                              Use higher values for more creative responses, and lower values for more deterministic responses. 
                              Values can range from [0.0, 2.0]. Default value is 1.0
                output_format - output format: "text" or "json". Default is "text"
                candidate_count - specifies the number of generated responses to return. Currently, this value can only be set to 1.
                system_instructions_source - optional argument: the name of the file containing system instructions to the model. Default is None
                
            Note that the API keys must exist (i.e. exported) in the environment: GEMINI_API_KEY for Gemini, API_KEY for OpenAI.
            System and prompt files are assumed to be unstructured text. 
            They are also assumed to exist in the project resources/genres/<genre> folder, where <genre> :: 'horror' | 'noir' | 'romance'
            UNLESS a full path is provided.
        """
        self._default_prompt = GPTProvider.DEFAULT_PROMPT
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        self._genre = genre
        self._genre_folder = f"{self._resource_folder}/genres/{genre.value}"
        self._provider = provider
        self._model_name = model_name
        self._model = None
        
        self._prompt_source = prompt_source
        if prompt_source is None:
            self._prompt = self._default_prompt
        else:
            thesource = prompt_source.split(":")
            if len(thesource) == 1:    # just use the text
                self._prompt = thesource[0]
            else:
                if thesource[0] == "file":
                    self._prompt_source = thesource[1] if thesource[1].startswith("/") else f"{self._genre_folder}/{thesource[1]}"
                    self._set_prompt()
                elif thesource[0] == "text":
                    self._prompt = thesource[1]
                else:
                    self._prompt = self._default_prompt
        
        self._system_instructions_source = system_instructions_source
        self._system_instructions = None
        if system_instructions_source is not None:
            self._system_instructions_source = system_instructions_source if system_instructions_source.startswith("/") else f"{self._genre_folder}/{system_instructions_source}"
        self._set_system_instructions()
        
        self._candidate_count = candidate_count
        self._output_format = output_format.lower()
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
    def genre(self)->GenreType:
        return self._genre
    
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
            This can be a text (.txt) or image (.jpg, .png) file (images TBD)
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
    
    @property
    def system_instructions(self)->str:
        return self._system_instructions
    
    @system_instructions.setter
    def system_instructions(self, text):
        self._system_instructions = text
    
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

    @property
    def default_prompt(self)->str:
        return self._default_prompt
    
    @default_prompt.setter
    def default_prompt(self, prompt):
        self._default_prompt = prompt

    

'''
Created on Nov 7, 2024

@author: don_bacon
'''

import google.generativeai as genai
import argparse
import os, sys
from game.gameConstants import GPTProviders, CardType, GenreType
from game.gptProvider import GPTProvider
from game.geminiGPTProvider import GeminiGPTProvider
from game.openAIGPTProvider import OPenAIGPTProvider
from game.environment import Environment
import typing_extensions as typing
from google.ai.generativelanguage_v1.types.generative_service import GenerateContentResponse
from openai import OpenAI
from pydantic import BaseModel

class StorySnippet(typing.TypedDict):
    line_number: int
    title: str
    story_text: str

class Card(BaseModel):
    line:int
    content:str

class Cards(BaseModel):
    cards:list[Card]

class PromptRunner(object):
    """
        Create a generative AI model and generate responses from text prompts.
    """
    
    def __init__(self, genre:str, provider:GPTProviders, model_name:str, card_type:CardType, \
                 prompt_source:str=None, system_instructions_source:str=None,  \
                 temperature=1.0, output_format="text", candidate_count=1):
        """
            Create and initialize a PromptRunner.
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
        """
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        self._genre_folder = f"{self._resource_folder}/genres/{genre}"
        self._provider = provider
        self._model_name = model_name
        
        self._model = None
        self._prompt = None
        self._prompt_source = prompt_source    # could be None
        self._system_instructions = None
        self._system_instructions_source = system_instructions_source    # could be None
        self._candidate_count = candidate_count
        self._output_format = output_format
        self._content = None    # latest result of generate_content
        # . 
        # Use higher values for more creative responses, and lower values for more deterministic responses. 
        # Values can range from [0.0, 2.0].
        self._temperature = temperature
        if prompt_source is not None:
            self.prompt_source = prompt_source
        if system_instructions_source is not None:
            self._system_instructions_source = system_instructions_source
            
        if provider is GPTProviders.GEMINI:
            self._model = genai.GenerativeModel(model_name) if self._system_instructions is None else genai.GenerativeModel(model_name, system_instructions=self._system_instructions)
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            self.configure_model(temperature, output_format)
        else:   # OpenAI
            api_key = os.environ["OPENAPI_API_KEY"]
            print(f"{provider} not implemented, but coming soon!")
            
    def configure_model(self, temp:float, output_format:str):
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
    
    def generate_content(self, prompt:str=None)->GenerateContentResponse:
        if prompt is not None:
            self._prompt = prompt
        response = self.model.generate_content(self._prompt, generation_config=self._generation_config)
        # self._content = response.text
        return response.text
        
    @property
    def model(self):
        return self._model
    
    @property
    def model_name(self)->str:
        return self._model_name
    
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
    def prompt_source(self, filename):
        """Read the file identified by path and save as the prompt
            TODO support image files
        """
        if filename is not None:
            path = f"{self._genre_folder}/{filename}"
            with open(path, "r") as fp:
                self._prompt = fp.read()
            fp.close()
            
    @property
    def system_instructions_source(self)->str|None:
        return self._system_instructions
    
    @system_instructions_source.setter
    def system_instructions_source(self, filename):
        """Read the file identified by filename and save as system_instructions
        """
        if filename is not None:
            path = f"{self._genre_folder}/{filename}"
            with open(path, "r") as fp:
                self._system_instructions = fp.read()
            fp.close()
    
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

def main():
    parser = argparse.ArgumentParser(description="Generate content from a text prompt")
    parser.add_argument("--provider", help="The name of the provider for this GPT", type=str, choices=["gemini","openai"], default=None)
    # parser.add_argument("--system", help="Name of the file containing system instructions.", type=str, default=None)
    parser.add_argument("--genre", "-g", help="The story genre: horror, noir, or romance.", type=str, choices=["horror", "noir"],  default=None)
    parser.add_argument("--model", "-m", help="Model name", type=str, choices=['gemini-1.5-flash', 'gpt-4o', 'o1-preview', 'o1-mini'],  default=None )
    # parser.add_argument("--prompt", "-p", help="Provide a text prompt", type=str, default=None)
    parser.add_argument("--prompt_source", "-p", help="file:<The name of the file containing the prompt/training>, text:<the actual text prompt>", default=None)
    parser.add_argument("--system_instructions", "-s", help="Name of the file containing system instructions", type=str, default=None)
    parser.add_argument("--count", help="Candidate count - #responses", type=int, default=1)
    parser.add_argument("--temperature", "-t", help="temperature controls the randomness of the output", type=float, default=1.0)
    parser.add_argument("--format", "-f", help="Output format", type=str, choices=["text", "json"], default="text")
    card_types = [x.value for x in CardType]   # Title, Story, Opening, Opening/Story, Closing, Action
    parser.add_argument("--card_type", "-c", help="Optional Card type, default is Story", type=str, choices=card_types, default="Story")
    
    args = parser.parse_args()
    # if prompt_source is None, the default_prompt specified in GPTProvider is used
    if args.prompt_source is None:
        default_prompt = GPTProvider.DEFAULT_PROMPT
        print(f"Warning: using the default prompt '{default_prompt}'")
    card_type = CardType[args.card_type.upper()]
    provider = GPTProviders[args.provider.upper()]
    genre = GenreType[args.genre.upper()]
    if provider is GPTProviders.GEMINI:
        gptProvider = GeminiGPTProvider(genre, provider, args.model, card_type=card_type, \
                                   prompt_source=args.prompt_source, system_instructions_source=args.system_instructions, \
                                   temperature=args.temperature, \
                                   output_format=args.format, candidate_count=args.count  )

    elif provider is GPTProviders.OPENAI:
        gptProvider = OPenAIGPTProvider(genre, provider, args.model, card_type=card_type, \
                                   prompt_source=args.prompt_source, system_instructions_source=args.system_instructions, \
                                   temperature=args.temperature, \
                                   output_format=args.format, candidate_count=args.count  )
    prompt = gptProvider.prompt
    gptProvider.generate_content(prompt)
    response_text = gptProvider.content
    print(response_text)
        
    sys.exit()

if __name__ == '__main__':
    main()
    
    
    
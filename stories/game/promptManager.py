'''
Created on Nov 7, 2024

@author: don_bacon
'''

import google.generativeai as genai
import argparse
import os, sys
from game.gameConstants import GPTProvider
from google.ai.generativelanguage_v1.types.generative_service import GenerateContentResponse

class PromptManager(object):
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
        The format of the responses  - for example numbering, including a title - can be controlled by the prompt itself.
    """
    
    def __init__(self, provider:GPTProvider=GPTProvider.GEMINI, model_name:str='gemini-1.5-flash', prompt_source:str=None, temperature=1.0, candidate_count=1):
        """
            Create and initialize a PromptManager.
            Arguments:
                provider - the provider of the underlying API: GPTProvider.GEMINI or GPTProvider.OPENAI
                model_name - the name of the provider's model to use
                prompt_source - optional argument. If included, the name of the file containing the prompt.
                                TODO - add MongoDB support
                temperature - temperature controls the randomness of the output. 
                              Use higher values for more creative responses, and lower values for more deterministic responses. 
                              Values can range from [0.0, 2.0].
                candidate_count - specifies the number of generated responses to return. Currently, this value can only be set to 1.
        """
        self._provider = provider
        self._model_name = model_name
        self._model = None
        self._prompt = None
        self._prompt_source = prompt_source
        self._candidate_count = candidate_count
        
        # . 
        # Use higher values for more creative responses, and lower values for more deterministic responses. 
        # Values can range from [0.0, 2.0].
        self._temperature = temperature
        if prompt_source is not None:
            self.prompt_source = prompt_source
            
        if provider is GPTProvider.GEMINI:
            self._model = genai.GenerativeModel(model_name)
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            self.configure_model()
        else:
            print(f"{provider} not implemented, but coming soon!")
            
    def configure_model(self):
        # [START configure_model_parameters]
        self._generation_config = genai.types.GenerationConfig(candidate_count=self._candidate_count, temperature=self.temperature )
        # [END configure_model_parameters]
    
    def generate_content(self, prompt:str=None)->GenerateContentResponse:
        if prompt is not None:
            self._prompt = prompt
        response = self.model.generate_content(self._prompt, generation_config=self._generation_config)
        return response.text
        
    @property
    def model(self):
        return self._model
    
    @property
    def model_name(self)->str:
        return self._model_name
    
    @property
    def provider(self)->GPTProvider:
        return self._provider
    
    @property
    def prompt(self)->str:
        return self._prompt
    
    @prompt.setter
    def prompt(self, the_prompt):
        self._prompt = the_prompt
    
    @property
    def prompt_source(self)->str:
        """The name of the file containing the prompt.
            This can be a text (.txt) or image (.jpg, .png) file
        """
        return self.prompt_source
    
    @prompt_source.setter
    def prompt_source(self, path):
        """Read the file identified by path and save as the prompt
            TODO support image files
        """
        with open(path, "r") as fp:
            self._prompt = fp.read()
        fp.close()
    
    @property
    def temperature(self)->float:
        return self._temperature
    
    @temperature.setter
    def temperature(self, value:float):
        self._temperature = value
        # reconfigure the model
        self.configure_model()

def main():
    parser = argparse.ArgumentParser(description="Generate content from a text prompt")
    parser.add_argument("--provider", help="The name of the provider for this GPT", type=str, choices=["gemini","openai"], default="gemini")
    parser.add_argument("--model", "-m", help="Model name", type=str, default='gemini-1.5-flash' )
    parser.add_argument("--prompt", "-p", help="Provide a text prompt", type=str, default=None)
    parser.add_argument("--source", "-s", help="The path to the file or MongoDB collection containing the prompt/training", default=None)
    parser.add_argument("--count", "-c", help="Candidate count - #responses", type=int, default=1)
    parser.add_argument("--temperature", "-t", help="temperature controls the randomness of the output", type=float, default=1.0)
    
    args = parser.parse_args()
    if  not (args.prompt is None and args.file is None):    # need an embedded prompt, or a file containing a prompt
        provider = GPTProvider[args.provider.upper()]
        prompt_manager = PromptManager(provider=provider, model_name=args.model, prompt_source=args.source, temperature=args.temperature, candidate_count=args.count)
        response_text = prompt_manager.generate_content(args.prompt)
        print(response_text)
        # configure the responses to be more creative
        prompt_manager.temperature = 2.0
        response_text = prompt_manager.generate_content(args.prompt)
        print(response_text)     
    
    else:
        print("Please provide a prompt: '--prompt <your text prompt>'")
    
    sys.exit()

if __name__ == '__main__':
    main()
    
    
    
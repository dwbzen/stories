'''
Created on Nov 7, 2024

@author: don_bacon
'''

import google.generativeai as genai
import argparse
import json
import sys
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

class PromptRunner(object):
    """
        Create a generative AI model and generate responses from text prompts.
    """
    
    def __init__(self):
        ...
 
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
    content_dict = gptProvider.content_dict
    response_text = gptProvider.content if content_dict is None else json.dumps(content_dict, indent=2)
    
    print(response_text)
        
    sys.exit()

if __name__ == '__main__':
    main()
    
    
    
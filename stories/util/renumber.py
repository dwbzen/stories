'''
Created on Dec 31, 2024

@author: don_bacon
'''

import argparse
from game.environment import Environment
from game.commandResult import CommandResult
import sys
import json

class Renumber(object):
    """
        Create a generative AI model and generate responses from text prompts.
    """
    
    def __init__(self, genre:str, source:str, start_line:int, output_file:str):
        self.genre = genre
        self.source_file = source
        self.start_line = start_line
        self.output_file = output_file
        self.content = {}
        
    def renumber(self)->CommandResult:
        content = None
        with open(self.source_file, "r") as fp:
            content = fp.read()
        fp.close()
        if content is None:
            message = f"Invalid file: {self.source_file}"
            return CommandResult(CommandResult.ERROR, message=message)
        contact_dict = json.loads(content)
        cards = contact_dict["cards"]
        linenum = self.start_line
        count = 0
        for card in cards:
            card["line"] = linenum
            linenum += 1
            count += 1
            
        jtext = json.dumps(contact_dict, indent=2)
        with open(self.output_file, "w") as fp:
            fp.write(jtext)
        fp.close()
        
        message = f"{count} lines renumbered, sent to output file: {self.output_file}"
        self.content = contact_dict
        return CommandResult(CommandResult.SUCCESS, message=message)

def main():
    parser = argparse.ArgumentParser(description="Renumber the lines in a JSON file")
    parser.add_argument("--source", "-s", help="<The name of the JSON file>", default=None)
    parser.add_argument("--genre", "-g", help="The story genre: horror, noir, or romance.", type=str, choices=["horror", "noir"],  default=None)
    parser.add_argument("--line", "-l", help="Starting new line number", type=int, default=0)
    parser.add_argument("--output_file", help="Name of the output file. The source file is updated if no output file is specified", type=str, default=None)
    args = parser.parse_args()
    
    env = Environment.get_environment()
    resource_folder = env.get_resource_folder()     # base resource folder
    genre = args.genre
    genre_folder = f"{resource_folder}/genres/{genre}"
    source_file = f"{genre_folder}/{args.source}"
    output_file = source_file if args.output_file is None else f"{genre_folder}/{args.output_file}"
    start_line = args.line
    
    renum = Renumber(genre, source_file, start_line, output_file)
    result:CommandResult = renum.renumber()
    print(result.message)


if __name__ == '__main__':
    main()
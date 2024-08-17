'''
Created on Aug 15, 2024

@author: don_bacon
'''
import json
import argparse
from game.environment import Environment
from game.gameConstants import GenreFilenames, GenreType, CardType

class ConversionUtils(object):
    """Convert genre text file to JSON format
        Genre file prefixes given by GenreFilenames Enum.
        Complete filename for a given card type is the GenreFilenames.<card type> + <genre> + ".txt"
        For example, "opening_lines_horrow.txt" (GenreFilenames.OPENING)
        The JSON file has the same name with a .json extension
    """

    def __init__(self, genre_type:str, card_type:str):
        """
        """
        self.genre_type = GenreType[genre_type.upper()]  # horror, noir
        self.card_type = card_type
        self.cardType = CardType[card_type.upper()].value               # Title, Opening, Opening/Story, Story, Closing
        self.genre_filename = GenreFilenames[card_type.upper()].value   # titles, opening, opening_story, story, closing
        self.env = Environment.get_environment()
        self.resource_folder = self.env.get_resource_folder()     # base resource folder
        self.filename = f"{self.genre_filename}{self.genre_type.value}"
        self.genre_file_path = f"{self.resource_folder}/genres/{self.genre_type.value}/{self.filename}.txt"    # for example "/Compile/stories/resources/genres/horror"
        self.json_file_path =  f"{self.resource_folder}/genres/{self.genre_type.value}/{self.filename}.json" 
        print(f"loading {self.genre_file_path}")
    
    def convert(self):
        print(f"converting {self.genre_file_path} to JSON file {self.json_file_path}")
        index = f'"cardType" : "{self.cardType}"'
        json_text = '{' + f'{index},\n "cards" : ['
        num = 1
        with open(self.genre_file_path) as fp:
            for line in fp:
                line = line.lstrip().rstrip()           # delete left padding and trailing \n
                if line=="" or line.startswith("--"):   # skip comment lines
                    continue
                line = line.replace('"', '\\"')     # embedded quotes must be escaped twice, as in \\" 
                json_line = '{' + f'"line": {num}, "content":"{line}"' + '}'
                json_text = f"{json_text}\n{json_line},"
                num += 1
        json_text = json_text[:-1]
        json_text = json_text + "\n] }"
        print(json_text)
        fp.close()
        fp = open(self.json_file_path, "w")
        fp.write(json_text)
        fp.close()
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert a genre text file to JSON")
    card_types = ["title", "opening", "opening_story", "story", "closing"]       # CardType
    card_type_choices = card_types.append("all")    # to convert all 5 card types
    genres = ["horror","romance","noir"]
    parser.add_argument("--genre", help="Story genre", type=str, choices=genres, default="horror")
    parser.add_argument("--cardtype", help="CardType", type=str, choices=card_type_choices)
    
    args = parser.parse_args()
    if args.cardtype == "all":
        print("All option not available")
    else:
        conversion_util = ConversionUtils(args.genre, args.cardtype)
        conversion_util.convert()


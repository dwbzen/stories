'''
Created on Dec 7, 2023

@author: don_bacon
'''
from enum import Enum
from typing import Dict
import json

class GameParametersType(Enum):  # A.K.A. game mode
    TEST = "test"
    PROD = "prod"
    CUSTOM = "custom"

class GenreType(Enum):
    HORROR = "horror"
    NOIR = "noir"
    ROMANCE = "romance"

class CardType(Enum):
    TITLE = "Title"
    OPENING = "Opening"
    OPENING_STORY = "Opening/Story"
    STORY = "Story"
    CLOSING = "Closing"
    ACTION = "Action"

class CardTypeEncoder(json.JSONEncoder):
    def encode(self, obj):
        # print("CLS")
        if isinstance(obj, dict):
            message = [""]
            for k in obj.keys():
                message.append(f"'{k}':{str(obj[k])}")
            message.append("")
            message = message[1:len(message)-2]
            message = ",".join(message)
            return "{" + message + "}"
        # let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
    
class GenreFilenames(Enum):
    TITLES = "titles_"
    OPENING = "opening_lines_"
    OPENING_STORY = "opening_storylines_"
    STORY = "storylines_"
    CLOSING = "closings_"

class ActionType(Enum):
    MEANWHILE = "meanwhile"
    TRADE_LINES = "trade_lines"
    STEAL_LINES = "steal_lines"
    STIR_POT = "stir_pot"
    DRAW_NEW = "draw_new"
    CHANGE_NAME = "change_name"
    REORDER_LINES = "reorder_lines"
    COMPOSE = "compose"

class GameConstants(object):
    '''
    Define global constants
    '''
    COMMANDS = [
            'add', 'deal', 'discard', 'done', 'draw', 'end', 
            'game_status', 'help', 'info', 'insert', 
            'list', 'list_numbered', 'ln', 'log_message', 'ls', 
            'next', 'play', 'rank', 'read', 'rn', 'replace',
            'save', 'set', 'show', 'start', 'status' ]
    
    CHARACTERS = ['Michael', 'Nick', 'Samantha', 'Vivian']      # character names as they appear in the story files
    CARD_TYPES = [CardType.ACTION, CardType.TITLE, CardType.OPENING, CardType.OPENING_STORY, CardType.STORY, CardType.CLOSING]
     
    def __init__(self, params:Dict={} ):
        '''
        Constructor
        '''
        self._params = params
        
    @property
    def params(self) -> Dict:
        return self._params
    
    @params.setter
    def params(self, value:Dict):
        self._params = value
    
    @staticmethod
    def get_genre_filenames(genre:GenreType)->Dict:
        #
        # There are 5 story card text files for each genre, loaded from the project resources/genres/<genre> folder.
        # currently genre :: "horror" | "noir" | "romance"
        #
        filenames = {CardType.TITLE : f"{GenreFilenames.TITLES.value}{genre.value}.txt", \
                     CardType.OPENING : f"{GenreFilenames.OPENING.value}{genre.value}.txt", \
                     CardType.OPENING_STORY : f"{GenreFilenames.OPENING_STORY.value}{genre.value}.txt", \
                     CardType.STORY : f"{GenreFilenames.STORY.value}{genre.value}.txt", \
                     CardType.CLOSING : f"{GenreFilenames.CLOSING.value}{genre.value}.txt"
         }
        return filenames

    

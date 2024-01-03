'''
Created on Dec 7, 2023

@author: don_bacon
'''
from enum import Enum
from typing import Dict

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

class GameConstants(object):
    '''
    Define global constants
    '''
    COMMANDS = ['add', 'deal', 'discard', 'done', 'draw', 'end', 
            'game_status', 'help', 'info', 'list', 'log_message', 'next', 'play', 
            'read', 'save', 'set', 'start', 'status', 'who']
     
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
        
        filenames = {CardType.TITLE : f"{GenreFilenames.TITLES.value}{genre.value}.txt", \
                     CardType.OPENING : f"{GenreFilenames.OPENING.value}{genre.value}.txt", \
                     CardType.OPENING_STORY : f"{GenreFilenames.OPENING_STORY.value}{genre.value}.txt", \
                     CardType.STORY : f"{GenreFilenames.STORY.value}{genre.value}.txt", \
                     CardType.CLOSING : f"{GenreFilenames.CLOSING.value}{genre.value}.txt"
         }
        return filenames

    

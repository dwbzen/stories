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
    UNASSIGNED = "unassigned"       # use this instead of None

class CardType(Enum):
    TITLE = "Title"
    OPENING = "Opening"
    OPENING_STORY = "Opening/Story"
    STORY = "Story"
    CLOSING = "Closing"
    ACTION = "Action"

class PlayerLevel(Enum):
    """PlayerLevel determines what commands & action cards are available to a player
    """
    UNREGISTERED = "unregistered"
    FREE = "free"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    ELITE = "elite"

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
    TITLE  = "titles_"
    OPENING = "opening_lines_"
    OPENING_STORY = "opening_storylines_"
    STORY = "storylines_"
    CLOSING = "closings_"
    TRAINING_SYSTEM = "training_system_"
    TRAINING_USER = "training_user_"

class ActionType(Enum):
    MEANWHILE = "meanwhile"
    TRADE_LINES = "trade_lines"
    STEAL_LINES = "steal_lines"
    STIR_POT = "stir_pot"
    DRAW_NEW = "draw_new"
    CHANGE_NAME = "change_name"
    REORDER_LINES = "reorder_lines"
    COMPOSE = "compose"
    CALL_IN_FAVORS = "call_in_favors"

class ParameterType(Enum):
    BYPASS_ERROR_CHECKS =   "bypass_error_checks"
    STORY_LENGTH =          "story_length"
    MAX_CARDS =             "max_cards_in_hand"
    AUTOMATIC_DRAW =        "automatic_draw"
    CHARACTER_ALIAS =       "character_alias" 
    GAME_POINTS =           "game_points"
    ROUND_POINTS =          "round_points"
    RANDOMIZE_PICKS =       "randomize_picks"
    DATE_FORMAT =           "date_format"
    
class PlayMode(Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"
    COLLABORATIVE = "collaborative"
    UNASSIGNED = "unassigned"       # use this instead of None
    
class PlayerRole(Enum):
    PLAYER = "player"               # INDIVIDUAL or COLLABORATIVE PlayMode 
    TEAM_MEMBER = "team_member"     # TEAM PlayMode
    TEAM_LEAD = "team_lead"         # TEAM PlayMode
    DIRECTOR = "director"           # COLLABORATIVE PlayMode
    UNASSIGNED = "unassigned"       # Role not yet assigned to this player

class PlayerPermission(Enum):
    USER = "user"                   # default permission level
    ADMIN = "admin"                 # game administrator
    SUPER_USER = "super_user"       # super user has access to certain commands like draw_type

class Direction(Enum):
    RIGHT = "right"
    LEFT  = "left"
    ANY   = "any"    # random direction

class GPTProviders(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"

class GPTProviderKeyName(Enum):
    """The API key for a provider must exist in the runtime environment
       and the the name listed below.
    """
    GEMINI = "GEMINI_API_KEY"
    OPENAI = "OPENAI_API_KEY"

class GameConstants(object):
    '''
    Define global constants
    '''
    COMMANDS = [
            'add', 'add_team', 'deal', 'discard', 'done', 'draw', 'end', 
            'find', 'game_status', 'help', 'info', 'insert', 
            'list', 'list_numbered', 'ln', 'lnj', 'log_message', 'ls', 
            'next', 'pass_card', 'play', 'play_type', 'publish', 
            'rank', 'read', 're_read', 'rn', 'replace',
            'save', 'set', 'show', 'start', 'status', 'team_info', 'update' ]
    
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
        filenames = {CardType.TITLE : f"{GenreFilenames.TITLE.value}{genre.value}.txt", \
                     CardType.OPENING : f"{GenreFilenames.OPENING.value}{genre.value}.txt", \
                     CardType.OPENING_STORY : f"{GenreFilenames.OPENING_STORY.value}{genre.value}.txt", \
                     CardType.STORY : f"{GenreFilenames.STORY.value}{genre.value}.txt", \
                     CardType.CLOSING : f"{GenreFilenames.CLOSING.value}{genre.value}.txt"
         }
        return filenames

    

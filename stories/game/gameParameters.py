'''
Created on Dec 9, 2023

@author: don_bacon
'''
   
from typing import Dict, List
import json

class GameParameters(object):
    '''
    Encapsulates global game parameters for this game edition.
    There are 4 gameParameter files per edition:
        gameParameters_prod.json    - for production runs
        gameParameters_test.json    - for testing
        gameParameters_custom.json  - for custom testing
        gameParameters.json    - default parameters file (when _test or _prod is not specified)
        
    Game parameters are:
        "description" - a text description of the parameters file.
        "date_format" - the date format to use, for the US it's yyyy-mm-dd, other countries use yyyy-dd-mm
        "game_points" - game points to determine a winner, typically 20, can also be set on the command line with --points
        "bypass_error_checks" - bool (0 or 1), if True certain error checks, for example the command sequence, are ignored.
                                This can be helpful when debugging.
        "story_length" - the minimum number of StoryCards that must be played in a game before a point penalty is accessed.
                         This count is exclusive of action story cards.
        "randomize_picks" - bool (0 or 1). If True then in instances where a player must pick a card in their hand,
                            for example when passing a card to the player's left in "stir_pot" action,
                            a random pick is done automatically.
        "character_aliases" - a dict of alias names to use in place of the standard names of Michael, Nick, Samantha, and Vivian.
        "max_cards_in_hand" - the maximum number of cards that can be held in a player's hand.
        "automatic_draw" - bool, if True then after a player plays a card from their hand, a new card is drawn automatically.
                            Otherwise the player must issue a 'draw' command.
    '''


    def __init__(self, params:dict):
        self._game_parameters = params

        self._character_aliases = params.get("character_alias")
        self._game_points = params.get("game_points", 20)
        self._date_format = params.get("date_format", "yyyy-dd-mm")
        self._description = params.get("description", "No description")
        self._story_length = params.get("story_length", 10)
        self._bypass_error_checks = params.get("bypass_error_checks", 0) == 1
        self._randomize_picks = params.get("randomize_picks", 0) == 1
        self._round_points:Dict[str,int] = params.get("round_points", {"1" : 5, "2" : 3, "3" : 1, "4" : 0})
        self._max_cards_in_hand = params.get("max_cards_in_hand", 10)
        self._automatic_draw = params.get("automatic_draw", 0) == 1
        self._settable_parameter_names = ["bypass_error_checks", "story_length", "max_cards_in_hand", "automatic_draw", "character_alias" ]
        self._id = params.get("_id", "None")
        self._game_parameters["bypass_error_checks"] = self._bypass_error_checks
        self._game_parameters["randomize_picks"] = self._randomize_picks
        self._game_parameters["automatic_draw"] = self._automatic_draw
        
        # MongoDB parameters
        self.db_url = params.get("DB_URL", "mongodb://localhost:27017/")
        self.db_name = params.get("DB_NAME", "stories")
        self.db_name_genres = params.get("DB_NAME_GENRES", "genres")
        
    def game_parameters(self):
        return self._game_parameters
    
    def get_param(self, param_name):
        return self._game_parameters.get(param_name, None)
    
    @property
    def settable_parameter_names(self)->List[str]:
        return self._settable_parameter_names
    
    @property
    def game_points(self):
        return self._game_points
    
    @game_points.setter
    def game_points(self, value):
        self._game_points = value
        self._game_parameters["game_points"] = value
    
    @property
    def character_aliases(self)->dict:
        return self._character_aliases
    
    @property
    def bypass_error_checks(self)->bool:
        """If bypass_error_checks is True certain error checking is bypassed
            including errors involving drawing and discarding cards.
            Default value if not present in the gameParameters file is False.
        """
        return self._bypass_error_checks
    
    @bypass_error_checks.setter
    def bypass_error_checks(self, value:bool):
        self._bypass_error_checks = value
        self._game_parameters["bypass_error_checks"] = value
    
    @property
    def randomize_picks(self)->bool:
        return self._randomize_picks
    
    @randomize_picks.setter
    def randomize_picks(self, value:bool):
        self._randomize_picks = value
        self._game_parameters["randomize_picks"] = value
    
    @property
    def story_length(self)->int:
        return self._story_length
    
    @story_length.setter
    def story_length(self, value:int):
        self._story_length = value
        self._game_parameters["story_length"] = value
        
    @property
    def round_points(self)->Dict[str,int]:
        return self._round_points
    
    @property
    def max_cards_in_hand(self)->int:
        return self._max_cards_in_hand
    
    @max_cards_in_hand.setter
    def max_cards_in_hand(self, val):
        self._max_cards_in_hand = val
        self._game_parameters["max_cards_in_hand"] = val
        
    @property
    def automatic_draw(self)->bool:
        return self._automatic_draw
    
    @automatic_draw.setter
    def automatic_draw(self, val):
        self._automatic_draw = val
        self._game_parameters["automatic_draw"] = val
    
    def __str__(self)->str:
        return str(self._game_parameters)
    
    def to_JSON(self, indent=2):
        return json.dumps(self._game_parameters, indent=indent)
    
    
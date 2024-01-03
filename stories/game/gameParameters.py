'''
Created on Dec 9, 2023

@author: don_bacon
'''
   

class GameParameters(object):
    '''
    Encapsulates global game parameters for this game edition.
    There are 4 gameParameter files per edition:
        gameParameters_prod.json    - for production runs
        gameParameters_test.json    - for testing
        gameParameters_custom.json    - for custom testing
        gameParameters.json    - default parameters file (when _test or _prod is not specified)
    '''


    def __init__(self, params:dict):
        self._game_parameters = params

        self._default_game_points = params.get("default_game_points", 20)
        self._date_format = params.get("date_format", "yyyy-dd-mm")
        self._description = params.get("description", "No description")
    
    def game_parameters(self):
        return self._game_parameters
    
    def get_param(self, param_name):
        return self._game_parameters.get(param_name, None)
    
    @property
    def default_game_points(self):
        return self._default_game_points
    
    @default_game_points.setter
    def default_game_points(self, value):
        self._default_game_points = value
        
    
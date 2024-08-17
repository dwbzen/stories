'''
Created on Aug 15, 2024

@author: don_bacon
'''

from typing import Dict, List
import json
import pymongo
import argparse
from game.gameConstants import GameParametersType, GenreType, CardType, ActionType, PlayMode, PlayerRole
from game.gameParameters import GameParameters
from game.commandResult import CommandResult
from game.environment import Environment
from game.cardDeck import CardDeck

class DataManager(object):
    """
        Manage data from a given source: text file or MongoDB
        Connection info is in the .env file in the project root folder.
        Stories game has 2 Mongo databases: stories and genres.
    """

    def __init__(self, source:str, game_parameters_type:str, genre:str):
        """Construct a stateful DataManager
            Arguments:
                source - the data source: "text", for .txt files, or "mongo" for MongoDB
                game_parameters_type - "test", "prod", "custom"
        """
        self._source = source
        self._genre = genre
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        self._game_parameters_type = GameParametersType[game_parameters_type.upper()]      # can be "test", "prod", or "custom"
        self._resource_folder = self._env.get_resource_folder()     # base resource folder for example, "/Compile/stories/resources"
        self.active = True
        self._card_deck = None
        
        if source == "mongo":
            result = self.mongo_init()
            if not result.is_successful():
                self.active = False
                print(result.message)
                self._game_parameters = None
        if self.active:
            self.load_parameters(source, game_parameters_type)
            self._card_deck = self.load_story_cards(source, genre)
        
        
    def mongo_init(self)->CommandResult:
        """Initializes MongoDB client info using the default gameParameters.json text file
        """
        game_parameters_filename = f'{self._resource_folder}/gameParameters.json'
        with open(game_parameters_filename, "r") as fp:
            jtxt = fp.read()
            game_parameters = GameParameters(json.loads(jtxt))
        fp.close()
        self._db_url = game_parameters.db_url
        self._db_name = game_parameters.db_name
        self._db_name_genres = game_parameters.db_name_genres
        try:
            mongo_client = pymongo.MongoClient(self._db_url)
            self._stories_db = mongo_client[self._db_name]
            self._genres_db = mongo_client[self._db_name_genres]
            self._mongo_client = mongo_client
            result = CommandResult(CommandResult.SUCCESS)
        except Exception as ex:
            message = f'MongoDB error, exception: {str(ex)}'
            result = CommandResult(CommandResult.ERROR,  message,  False, exception=ex)
        
        return result

    def load_parameters(self, source:str, game_parameters_type:str)->CommandResult:
        """Loads stories GameParameters from a specified source.
            Arguments:
                source - 'mongo' or 'text'
                game_parameters_type - "test", "prod", "custom"
            Returns a CommandResult with return_code of SUCCESS or ERROR.
        """
        result = CommandResult()
        if source == "mongo":
            collection = self._stories_db["parameters"]
            query:dict = {"Title" : game_parameters_type}
            docs_cursor = collection.find(query)   # returns a cursor
            for doc in docs_cursor:
                doc["_id"] = str(doc["_id"])       # because ObjectId can't be serialized
                self._game_parameters = GameParameters( doc)
                result = CommandResult(CommandResult.SUCCESS,f"{game_parameters_type} loaded from DB")
        else:
            game_parameters_filename = f'{self._resource_folder}/gameParameters_{game_parameters_type}.json'
            with open(game_parameters_filename, "r") as fp:
                jtxt = fp.read()
                self._game_parameters = GameParameters(json.loads(jtxt))
            fp.close()
            result = CommandResult(CommandResult.SUCCESS,f"{game_parameters_filename} loaded")
            
        return result
    
    def load_story_cards(self, source, genre)->CardDeck:
        """Loads the stories CardDeck from a specified source for a given genre
            Arguments:
                source - 'mongo' or 'text'
                genre - a valid story genre, currently horror or noir
            Returns a CardDeck if successful or None if there's an error.   
        """
        if source == "mongo":
            result = self.load_story_cards_db(genre)
        else:
            result = self.load_story_cards_text(genre)
        return result
    
    def load_story_cards_text(self, genre)->CardDeck:
        pass
    
    def load_story_cards_db(self, genre)->CardDeck:
        pass

    @property
    def game_parameters(self)->GameParameters:
        return self._game_parameters
    
    @property
    def card_deck(self)->CardDeck:
        return self._card_deck

if __name__ == '__main__':
    """A quick test
    """
    parser = argparse.ArgumentParser(description="DataManager for text or MongoDB")
    parser.add_argument("--source", help="mongo or text", type=str, choices=['mongo','text'], default='text')
    parser.add_argument("--params", help="Parameters type", type=str, choices=['prod','test','custom'], default='test')
    parser.add_argument("--genre", help="Story genre", type=str, choices=["horror","romance","noir"], default="horror")
    args = parser.parse_args()
    # self._game_parameters_type = GameParametersType[game_parameters_type.upper()] 
    dm = DataManager(args.source, args.params.title(), args.genre)
    if dm.active:    # no errors
        game_parameters = dm.game_parameters
        print(game_parameters.to_JSON(indent=2))

    
    
'''
Created on Aug 15, 2024

@author: don_bacon
'''

from typing import List
import json
import pymongo
import argparse
import dotenv
from datetime import datetime
from game.gameConstants import GameParametersType, GenreType
from game.gameParameters import GameParameters
from game.commandResult import CommandResult
from game.environment import Environment
from game.cardDeck import CardDeck
from game.storyCard import StoryCard
from game.storyCardLoader import StoryCardLoader

class DataManager(object):
    """
        Manage data from a given source: text file or MongoDB
        Connection info is in the .env file in the project root folder.
        Stories game has 2 Mongo databases: stories and genres.
    """

    def __init__(self, source:str, game_parameters_type:str, genre:str, load_all:bool=False):
        """Construct a stateful DataManager
            Arguments:
                source - the data source: "text", for .txt files, or "mongo" for MongoDB
                game_parameters_type - "test", "prod", "custom"
                genre - "horror", "noir" or "romance"
                load_all - if True, load game parameters, story card template and story cards. Default is False.
        """
        self._source = source
        self._genre = GenreType[genre.upper()]
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder for example, "/Compile/stories/resources"
        self._game_parameters_type = GameParametersType[game_parameters_type.upper()]      # can be "test", "prod", or "custom"
        self._game_parameters = None
        self.active = True
        self._card_deck = None
        self._deck_cards = None
        
        if source == "mongo":
            result = self.mongo_init()
            if not result.is_successful():
                self.active = False
                print(result.message)
                self._game_parameters = None
        if load_all and self.active:
            self.load_parameters(source, game_parameters_type)
            self.load_story_card_template(source, self._genre, game_parameters_type)
            self.load_story_cards()
        
        
    def mongo_init(self)->CommandResult:
        """Initializes MongoDB client info using the .env project file
        """
        config = dotenv.dotenv_values(".env")
        self._db_url = config["DB_URL"]
        self._db_name = config["DB_NAME"]
        self._db_name_genres = config["DB_NAME_GENRES"]
        
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
            Sets self._game_parameters to the GameParameters instance.
        """
        result = CommandResult()
        if source == "text":
            game_parameters_filename = f'{self._resource_folder}/gameParameters_{game_parameters_type}.json'
            with open(game_parameters_filename, "r") as fp:
                jtxt = fp.read()
                self._game_parameters = GameParameters(json.loads(jtxt))
            fp.close()
            result = CommandResult(CommandResult.SUCCESS,f"{game_parameters_filename} loaded")
                        
        else:
            collection = self._stories_db["parameters"]
            query:dict = {"Title" : game_parameters_type}
            doc = collection.find_one(query)   # returns a cursor
            if doc is not None:
                doc["_id"] = str(doc["_id"])       # because ObjectId can't be serialized
                self._game_parameters = GameParameters( doc)
                result.message = f"{game_parameters_type} loaded from DB"
            else:
                result.return_code = CommandResult.ERROR
                result.message = f"Unable to load parameters from DB for {game_parameters_type}"
                
        return result
    
    def load_story_cards(self)->CardDeck:
        """Loads the stories CardDeck from a specified source for a given genre
            Arguments:
                source - 'mongo' or 'text'
                genre - a valid story genre, currently horror or noir
            Returns a CardDeck if successful or None if there's an error.   
        """
        loader = StoryCardLoader(self.source, self.genre, self.game_parameters, self._resource_folder, self.story_card_template)
        result = loader.load_cards()
        if result.is_successful():
            deck_cards = loader.deck_cards
            self._story_card_template["cards"] = deck_cards
            cards_loaded = len(deck_cards)
            result.message = f"{cards_loaded} cards loaded"
            self._deck_cards = deck_cards
        return result
    
    def load_story_card_template(self, source, genre:GenreType, game_parameters_type:str) ->CommandResult:
        story_card_template = {}
        result = CommandResult()
        if source == 'text':
            template_filename = f"{self._resource_folder}/story_cards_template_{game_parameters_type}.json"
            with open(template_filename, "r") as fp:
                jtxt = fp.read()
                template = json.loads(jtxt)    # returns a Dict
            fp.close()
            story_card_template["Help"] = template["Help"] + f" {genre.value}"
            story_card_template["card_types_list"] = template["card_types_list"]   # "Title", "Opening", "Opening/Story", "Story", "Closing"
            self._card_types_list = []
            #
            # convert the card types to lower case for use in commands
            # "title", "opening", "opening/story", "story", "closing", "action"
            #
            for ct in story_card_template["card_types_list"]:
                self._card_types_list.append(ct.lower())
                
            story_card_template["action_types_list"] = template["action_types_list"]
            story_card_template["card_types"] = template["card_types"]
            story_card_template["action_types"] = template["action_types"]
            story_card_template["characters"] = template["characters"]
            story_card_template["commands"] = template["commands"]
            story_card_template["command_details"] = template["command_details"]
            
            self._card_types = story_card_template["card_types"]
            self._card_type_counts = {}
            for c in self._card_types:    # dict
                card_type = c["card_type"]
                max_count = c["maximum_count"]
                self._card_type_counts[card_type] = max_count
            self._commands = template["commands"]
            self._command_details = template["command_details"]
            result.message = f"{template_filename} loaded"
        else:    # load from stories DB templates collection
            collection = self._stories_db["templates"]
            query:dict = {"Title" : game_parameters_type}
            story_card_template = collection.find_one(query)
            if story_card_template is not None:
                story_card_template["_id"] = str(story_card_template["_id"])       # because ObjectId can't be serialized
                result.message = f"story_cards_template_{game_parameters_type} loaded from DB"
            else:
                result.return_code = CommandResult.ERROR
                result.message = f"Unable to load templates from DB for {game_parameters_type}"
                
        self._story_card_template = story_card_template
        
        return result
    
    def update_game(self, game_id:str) ->CommandResult:
        """Update the endDate in a given game to current date/time
            If source is not "mongo" there is nothing to update:
            the StoriesGame end() function logs the end date/time.
        """
        result = CommandResult()
        if self._source == "mongo":
            collection = self._stories_db["games"]
            query = {"game_id" : game_id}
            theGame = collection.find_one(query)
            if theGame is not None:
                theGame["endDate"] = datetime.now()
                del theGame["_id"]    # _id is an immutable field
                replaced = collection.replace_one(query, theGame)     # filter, replacement
                result.message = f"{game_id} matched {replaced.matched_count}, replaced {replaced.modified_count}"
            else:
                result.return_code = CommandResult.WARNING
                result.message = f"Unable to load game {game_id}"
        else:
            pass    # nothing to update
        
        return result
    
    def add_game_story(self, game_id:str, player_id:str, story:dict) -> CommandResult:
        result = CommandResult()
        if self._source == "mongo":
            collection = self._stories_db["game_stories"]
            query = {"game_id" : game_id, "initials" : player_id}
            gs = collection.find_one(query)
            if gs is None:
                rec_id = f"{game_id}_{player_id}"
                story["id"] = rec_id
                story["game_id"] = game_id
                story["initials"] = player_id
                collection.insert_one(story)
            else:    # replace the existing one
                replaced = collection.replace_one(query, story)
                result.message = f"{game_id} matched {replaced.matched_count}, replaced {replaced.modified_count}"
        else:
            result.message = "TODO - write to a text file"
            
        return result
    
    def get_game_story(self, game_id:str, player_id:str) -> CommandResult:
        result = CommandResult()
        collection = self._stories_db["game_stories"]
        query = {"game_id" : game_id, "initials" : player_id}
        gs = collection.find_one(query)    # returns the MongoDB record as a Dict, or None if not found
        if gs is None:
            result.return_code = CommandResult.ERROR
            result.message = f"Story not found for {game_id} and {player_id}"
        else:
            pass
        
        result.properties = {"game_story" : gs}
        return result

    @property
    def game_parameters(self)->GameParameters:
        return self._game_parameters
    
    @property
    def source(self)->str:
        return self._source
    
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def card_deck(self)->CardDeck:
        return self._card_deck
    
    @property
    def story_card_template(self)->dict:
        return self._story_card_template
    
    @property
    def deck_cards(self)->List[StoryCard]:
        return self._deck_cards

if __name__ == '__main__':
    """A quick test to load a parameters file, story card template, and story cards.
    """
    
    parser = argparse.ArgumentParser(description="DataManager for text or MongoDB")
    parser.add_argument("--source", help="mongo or text", type=str, choices=['mongo','text'], default='text')
    parser.add_argument("--params", help="Parameters type", type=str, choices=['prod','test','custom'], default='test')
    parser.add_argument("--genre", help="Story genre", type=str, choices=["horror","romance","noir"], default="horror")
    args = parser.parse_args()
    # self._game_parameters_type = GameParametersType[game_parameters_type.upper()] 
    dm = DataManager(args.source, args.params, args.genre)
    if dm.active:    # no errors
        print("GameParameters:")
        game_parameters = dm.game_parameters
        print(game_parameters.to_JSON(indent=2))
        
        print("\nStory card template")
        story_card_template = dm.story_card_template
        print(story_card_template)
        
        print("\nStory Cards")
        print(dm.deck_cards)
        
        

'''
Created on Aug 12, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
import pymongo
from bson.objectid import ObjectId
from typing import Dict, List
import json, copy
import dotenv
import string
from uuid import uuid4
from pydantic import Field, BaseModel
from pymongo import MongoClient
from datetime import datetime

#from .playerManager import StoriesPlayer, StoriesPlayerManager

from game.storiesGameEngine import StoriesGameEngine
from game.storiesGame import StoriesGame
from game.player import Player
from game.commandResult import CommandResult
from game.gameConstants import PlayerRole
from game.dataManager import DataManager
from game import commandResult

class Game(BaseModel):
    """Persisted stories Games
    """
    id: str = Field(default=None)
    game_id:str = Field(default=None)
    genre:str = Field(...)    # GenreType - horror, noir, romance
    gameParametersType:str = Field(...)    # test, prod, or custom
    playMode:str = Field(...)     # collaborative, team, or individual
    installation_id:str = Field(...)
    createdBy: str = Field(default=None)
    createdDate: datetime = Field(default=datetime.now())
    startDate: datetime = Field(default=None)
    endDate: datetime = Field(default=None)
    errorNumber:int = Field(default=0)    # not persisted, obviously
    errorText:str = Field(default="")     # not persisted

class GameInfo(BaseModel):
    """The query/request view of a given Game
    """
    installation_id:str  = Field(...)
    game_id:str = Field(default="None")    # assigned when the StoriesGame is created
    genre:str = Field(...)    # GenreType - horror, noir, romance
    gameParametersType:str = Field(...)    # test, prod, or custom
    playMode:str = Field(...)     # collaborative, team, or individual
    # the initials of an individual player (individual play), or
    # the team lead (team play), or
    # the player initiating a collaborative game
    playerId:str = Field(default=None)
    # the role to assign a player added to a game: "player", "team_lead", "director", "team_member", "unassigned"
    playerRole:str = Field(default="unassigned")
    # True if this game is currently active - i.e. being played, False otherwise
    # set to True when a 'start' command is issued
    active:bool = Field(default=False)
    players: List[str] = Field(default=[])

class GameID(BaseModel):
    game_id:str = Field(...)
    playerId:str = Field(default=None)    # depending on context, player issuing the command, or next player
    message:str = Field(default=None)
    error_code:int = Field(default=0)

class PlayerInfo(BaseModel):
    game_id:str = Field(...)
    # the initials of an individual player
    playerId:str = Field(default=None)
    # the role to assign a player added to a game: "player", "team_lead", "director", "team_member", "unassigned"
    playerRole:str = Field(default="unassigned")
    permission_level:str = Field(default="user")    # "user", "admin", "super_user"
    status:str = Field(default=None)
    return_code:int = Field(default=0)

class CardInfo(BaseModel):
    """Specify a card by number plus any additional arguments needed for Action cards
    """
    game_id:str = Field(default="None")    # assigned when the StoriesGame is created
    initials: str = Field(...)
    card_number:str = Field(...)
    action_args:str = Field(default=None)

class DrawInfo(BaseModel):
    """
        This model is used to draw a specific card type: "title", "opening", "opening/story", "story", "closing", "action"
        For Action cards, also need to specify the action_type: "meanwhile", "trade_lines", "steal_lines", "stir_pot", "draw_new", "change_name"
        Drawing a specific type is useful for debugging. The user (player) must be a super-user.
    """
    game_id:str = Field(default="None")    # assigned when the StoriesGame is created
    initials: str = Field(...)
    card_type:str = Field(...)
    action_type:str = Field(default=None)

class Card(BaseModel):
    """StoryCard number, type and text
    """
    card_type:str = Field(...)
    card_number:str = Field(...)
    text:str = Field(...)
    
class StoriesGameManager(object):
    
    def __init__(self):
        """
            Constructor
        """
        self.games:Dict[str,StoriesGameEngine] = {}    # StoriesGameEngine has a StoriesGame reference, dict key is game_id
        self.config = dotenv.dotenv_values(".env")
        self.db_url = self.config["DB_URL"]
        self.db_name = self.config["DB_NAME"]    # stories DB
        result,message = self.db_init()
        if result:
            self.games_collection = self.stories_db["games"]
            self.players_collection = self.stories_db["players"]
        else:
            print(message)
        
        self.stories_game = None

    def db_init(self)->(bool,str):
        message = None
        result = True
        try:
            mongo_client = pymongo.MongoClient(self.db_url)
            self.stories_db = mongo_client[self.db_name]
            self.mongo_client = mongo_client
        except Exception as ex:
            message = f'MongoDB error, exception: {str(ex)}'
            result = False
            
        return result,message
        
    def create_game(self, gameInfo:GameInfo)->Game:
        #
        print(f"gameInfo: {gameInfo}")
        game_engine = StoriesGameEngine(installationId=gameInfo.installation_id)
        player_info = self.players_collection.find_one({"initials": gameInfo.playerId})    # returns the MongoDB players record as a Dict
        
        if player_info is None:
            return Game(errorNumber=1, errorText="No such user")
        
        gameInfo.players = [player_info["initials"]]

        theGame = Game(installation_id=gameInfo.installation_id, genre=gameInfo.genre, \
                       gameParametersType=gameInfo.gameParametersType, playMode=gameInfo.playMode)
        theGame.id = str(uuid4())
        theGame.createdBy = player_info["initials"]
        #
        # create the StoriesGame and if successful, persist Game to the DB
        #
        result = game_engine.create(gameInfo.installation_id, gameInfo.genre, 0, gameInfo.playMode, 'mongo', gameInfo.gameParametersType)
        if result.return_code != CommandResult.SUCCESS:
            theGame.errorNumber = 2
            theGame.errorText = "Could not create a StoriesGame"
        else:
            stories_game = game_engine.stories_game
            game_id = stories_game.game_id
            theGame.game_id = game_id
            
            #
            # add the initiating player to the game and assign the role, 
            # add the Game instance to the stories game collection, and start the game
            #
            self.games[game_id] = game_engine
            self._add_player(player_info, game_id, player_role=PlayerRole[gameInfo.playerRole.upper()])
            result = game_engine.start(what="game")
            if result.is_successful():
                theGame.startDate = datetime.now()
                self.games_collection.insert_one(jsonable_encoder(theGame))
        return theGame

    def add_player_to_game(self, playerInfo:PlayerInfo):
        player_info = self.players_collection.find_one({"initials": playerInfo.playerId})    # returns the MongoDB player record as a Dict
        #game_engine:StoriesGameEngine = self.games[playerInfo.game_id]
        if player_info is not None:
            player_role = PlayerRole[playerInfo.playerRole.upper()]
            result = self._add_player(player_info, playerInfo.game_id, player_role)
            if result.is_successful():
                playerInfo.status = f"{playerInfo.playerId} added to game {playerInfo.game_id}"
            else:
                playerInfo.status = result.message
                playerInfo.return_code = 1
        else:
            playerInfo.status = f"No such player {playerInfo.playerId} or game {playerInfo.game_id}"
        
        return playerInfo
    
    def _add_player(self, player_info:dict, gameId:str, player_role:PlayerRole=PlayerRole.PLAYER)->CommandResult:
        """Adds a player to the game with a given game_id
        """
        game_engine = self.games[gameId]
        command = f"add player {player_info['name']} {player_info['initials']} {player_info['login_id']} {player_info['email']}"
        result = game_engine.execute_command(command, aplayer=None)
        if result.is_successful():
            if player_role is PlayerRole.DIRECTOR:
                command = f"add director {player_info['name']} {player_info['initials']}"
                result = game_engine.execute_command(command, aplayer=None)
        return result
    
    def get_game_status(self, game_id):
        status = {}
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.game_status(indent=0)
            if result.is_successful():
                status = json.loads(result.message)
        return status
    
    def list_cards(self, game_id:str, initials:str)->dict:
        cards = {}
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.lnj(what='hand', initials=initials,  how='numbered')    # list numbered as JSON
            cards = json.loads(result.message)
        return cards
    
    def play_card(self, game_id:str, card_number:str, action_args:str)->str:
        """
            Play a story/action card from a player's hand OR the discard deck
            Arguments:
                card_id - the StoryCard number to play, 
                    or the string "last" to play the most recent card drawn,
                    or "#n" where n is the ordinal of the card listing.
                args - additional arguments for ACTION cards, depending on the ActionType of the card played.
        """
        #
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.play(card_number, action_args)
        else:
            result = CommandResult(CommandResult.ERROR, "invalid GameId")
        return result.message
    
    def draw_card(self, game_id:str, initials:str)->str:
        """Draw a new card for a given player and place it in their hand.
        """
        card = None
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result:CommandResult = game_engine.draw("new", initials=initials)    # draw a card for the current player in this game
            if result.is_successful():
                card = result.properties['text']
            else:
                card = result.message
        return card
    
    def draw_card_type(self, drawInfo:DrawInfo):
        card = None
        playerId = drawInfo.initials
        # player must be a super user
        game_id = drawInfo.game_id
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            
        return card
    
    def read_story(self, game_id:str, initials:str)->dict:
        """Reads the current story for this game_id and player (initials)
        """
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.read(True, initials, display_format="dict")
            props = result.properties
        else:
            result = CommandResult(CommandResult.ERROR, "invalid GameId")
            props = {"error_code" : 1, "message" : "invalid gameId"}
            
        return props
    
    def next_player(self, gameID:GameID)->dict:
        np = {"game_id" : gameID.game_id}
        if gameID.game_id in self.games:
            game_engine:StoriesGameEngine = self.games[gameID.game_id]
            result = game_engine.next()
            np["message"] = result.message
            np["playerId"] = result.properties["playerId"]
        else:
            result = CommandResult(CommandResult.ERROR, "invalid GameId")
            np["error_code"] = 1
            np["message"] =  f"invalid GameId: {gameID.game_id}"
            
        return np
    
    def end_game(self, gameID:GameID):
        game_id = gameID.game_id
        result = CommandResult()
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            theGame = self.get_game(game_id)
            theGame["endDate"] = datetime.now()
            del theGame["_id"]    # _id is an immutable field
            eng_result = game_engine.end(what="game")
            query = {"game_id" : game_id}
            replaced = self.games_collection.replace_one(query, theGame)     # filter, replacement
            result.message = f"{eng_result.message}: {game_id}  matched {replaced.matched_count}, replaced {replaced.modified_count}"
        else:
            result.message = f"invalid GameId: {gameID.game_id}"
            result.return_code = CommandResult.ERROR

        return result
    
    def get_game(self, game_id:str)->Game:
        """Gets the Game object corresponding the given game_id
            TODO - if the game is not active, restore the serialized StoriesGame
        """
        game:Game = None
        if game_id in self.games:
            game = self.games_collection.find_one({"game_id" : game_id})
            game["_id"] = game["id"]    # "_id" is an ObjectId and not iterable
        if game is None:
            print( f"GameId: {game_id} not found or is inactive")
            
        return game
    
    def get_help(self, game_id, card_or_command:str, action_type:str=None) ->dict:
        help = {"game_id" : game_id}
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.help(card_or_command, action_type)
            help["message"] = result.message
            help["error_code"] = result.return_code
        else:
            help["message"] = f"GameId: {game_id} not found or is inactive"
            help["error_code"] = 2
            
        return help
        
def main():
    # quick test
    gameManager = StoriesGameManager()
    initials="DWB"
    gameInfo = GameInfo(installation_id="DWBZen999", genre="horror", gameParametersType="test", playMode="collaborative", playerId=initials, playerRole="director")
    game:Game = gameManager.create_game(gameInfo)
    game_id = game.game_id
    print(f"created game {game_id}")
    cards = gameManager.list_cards(game_id, initials)
    print(cards)
    game_state = gameManager.get_game_status(game_id)
    print(game_state)
    result = gameManager.play_card(game_id, "#9", action_args=None)
    print(result)
    game = gameManager.get_game(game_id)
    print(game)
    gameId = GameID(game_id=game_id)
    result = gameManager.end_game(gameId)
    print(result.message)

if __name__ == '__main__':
    main()
'''
Created on Dec 8, 2023

@author: don_bacon
'''

from datetime import datetime
import json
from game.player import Player
from game.storiesObject import StoriesObject
from game.gameConstants import GameParametersType, CardType, PlayerRole
from typing import List

class GameState(StoriesObject):
    """Maintains the global state of a Stories game instance.
    
    """


    def __init__(self, game_id, total_points, game_parameters_type=GameParametersType.PROD):
        """Create and initialize a Stories GameState
            The GameState encapsulates the following dynamic game state properties:
                number_of_players
                players - a [Player]
                current_player_number -  the current player number (whose turn it is)
                current_player - a Player instance
                winning_player - a Player instance, None until the game determines a winner
                total_points - points needed to win 
                turns - total number of completed turns taken by all players
                turn_number - the current turn number
                game_start - the datetime when the game started (when this object was created)

        """
        self._players:List[Player] = []
        self._current_player_number = -1
        self._current_player = None
        self._total_points = total_points

        self._winning_player = None
        self._turns = 0
        self._turn_number = -1
        self._start_datetime:datetime = datetime.today()
        self._end_datetime:datetime = None
        self._game_complete = False
        self._game_parameters_type = game_parameters_type
        self._started = False
        self._game_id = game_id
        self._types_to_omit:List[CardType] = []    # CardTypes to omit when drawing. 
        self._round = 0    # the current round number
    
    @property
    def game_id(self):
        return self._game_id
    
    @game_id.setter
    def game_id(self, value):
        self._game_id = value
        
    def number_of_players(self):
        return len(self._players)

    @property
    def players(self) -> List[Player]:
        return self._players
    
    @property
    def winning_player(self) -> Player:
        return self._winning_player
    
    @winning_player.setter
    def winning_player(self, player:Player):
        self._winning_player = player
    
    @property
    def current_player(self) -> Player:
        return self._current_player
    
    @current_player.setter
    def current_player(self, player:Player):
        self._current_player = player
    
    @property
    def current_player_number(self):
        return self._current_player_number
    
    @current_player_number.setter
    def current_player_number(self, value):
        self._current_player_number = value
        
    @property
    def game_parameters_type(self) -> GameParametersType:
        return self._game_parameters_type
    
    @property
    def game_complete(self) -> bool:
        return self._game_complete
    
    @game_complete.setter
    def game_complete(self, value:bool):
        self._game_complete = value
        
    @property
    def started(self) -> bool:
        return self._started
    
    @started.setter
    def started(self, value:bool):
        self._started = value
    
    @property
    def total_points(self) ->int :
        return self._total_points
    
    @total_points.setter
    def total_points(self, value:int):
        self._total_points = value

    @property
    def turns(self):
        return self._turns
    
    @turns.setter
    def turns(self, value):
        self._turns = value
    
    @property
    def turn_number(self):
        return self._turn_number
    
    @turn_number.setter
    def turn_number(self, value):
        self._turn_number = value

    @property
    def start_datetime(self)->datetime:
        return self._start_datetime
    
    @start_datetime.setter
    def start_datetime(self, value:datetime):
        self._start_datetime = value
    
    @property
    def end_datetime(self)->datetime:
        return self.end_datetime
    
    @end_datetime.setter
    def end_datetime(self, value:datetime):
        self._end_datetime = value
        
    @property
    def round(self)->int:
        return self._round
    
    @round.setter
    def round(self, value:int):
        self._round = value
        
    @property
    def types_to_omit(self)->List[CardType]:
        """CardTypes to omit when drawing a new card.
            This list will either be empty, have 1 element or 2 elements.
            CardTypes will be CardType.TITLE, CardType.OPENING
        """
        return self._types_to_omit
    
    def add_card_type_to_omit(self, card_type:CardType):
        self._types_to_omit.append(card_type)
    
    def add_card_types_to_omit(self, card_types:List[CardType]):
        for ct in card_types:
            self._types_to_omit.append(ct)
    
    def get_elapsed_time(self) ->int:
        """Gets the elapsed game time
            Returns: the number minutes elapsed in the game
        """
        return self.get_gametime("minutes")
            
    def get_gametime(self, units="minutes") ->int:
        delta = datetime.now() - self.start_datetime
        gametime = delta.seconds//60 if units=="minutes" else delta.seconds
        return gametime
    
    def set_next_player(self)->int:
        """Returns the player number of the next player. And sets the value of current_player.
            If the current player is the first player (player number 0),
            the number of turns is incremented.
        
        """
        npn = self.get_next_player_number()
        self.current_player_number = npn
        self.current_player = self.players[self.current_player_number]
        self.current_player.can_roll = True
        if npn == 0:
            self.increment_turns()

        return self.current_player_number

    def increment_turns(self):
        self.turns += 1
        self.turn_number += 1
        
    def get_next_player_number(self, aplayer:Player=None):
        """Gets the next player's number relative to the current player, or a designated player.
            Arguments:
                aplayer - the Player instance to use, defaults to the current player if not specified.
        """  
        if aplayer is None:
            npn = 0 if self.current_player is None else (1 + self.current_player.number)
        else:
            npn = aplayer.number + 1
        return 0 if npn >= self.number_of_players() else npn
    
    def add_player(self, aplayer:Player)->int:
        """Add a Player to the game
            Argument: aplayer - a Player reference
            Returns: the player number added
        """
        aplayer.number = self.number_of_players()     # starts at 0
        self._players.append(aplayer)
        return aplayer.number
    
    def get_player_by_initials(self, initials):
        player = None
        for p in self.players:
            if p.player_initials.lower() == initials.lower():
                player = p
                break
        return player
    
    def get_players_by_role(self, role:PlayerRole)->List[Player]:
        """Get a list of Player by player_role.
            Arguments:
                role - A PlayerRole
            Returns:
                List[Player] who have that role.
        """
        players = [p for p in self.players if p.player_role is role]
        return players
    
    def get_team_players_by_role(self, team_name:str, role:PlayerRole)->List[Player]:
        """Get a list of Player in a given team by player_role.
            Arguments:
                team_name - the name of the team
                role - A PlayerRole
            Returns:
                List[Player] who have that role in the given team
        """
        players = [p for p in self.players if p.player_role is role and p.team_name == team_name]
        return players
    
    def get_all_team_members(self, team_name)->List[Player]:
        """Get a list of Player in a given team by player_role.
            Arguments:
                team_name - the name of the team
            Returns:
                List[Player] in the given team. Could be an empty list if the team doesn't exist or has no members.
        """
        players = [p for p in self.players if p.team_name == team_name]
        return players

    def to_JSON(self):
        gs = self.to_dict()
        return json.dumps(gs, indent=2)
    
    def to_dict(self) -> dict:
        gs = {"game_id" : self._game_id, "game_parameters_type" : self.game_parameters_type.value, \
              "number_of_players" : self.number_of_players(), "current_player_number" : self.current_player_number }
        gs["turns"] = self.turns
        gs["turn_number"] = self.turn_number

        gs["total_points"] = self.total_points

        gs["elapsed_time"] = self.get_elapsed_time()
        if self.winning_player is not None:
            gs["winning_player"] = self.winning_player.player_initials
        gs["game_complete"] = self.is_game_complete()

        players = []
        for player in self.players:
            players.append(player.to_dict())
        gs["players"] = players
        return gs

        
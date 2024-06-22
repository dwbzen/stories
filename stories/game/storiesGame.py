'''
Created on Dec 7, 2023

@author: don_bacon
'''
from game.commandResult import CommandResult
from game.storiesObject import StoriesObject
from game.player import Player
from game.environment import Environment
from game.gameConstants import GameConstants, GameParametersType, GenreType, CardType, ActionType
from game.gameParameters import GameParameters
from game.cardDeck import CardDeck
from game.storyCard import StoryCard
from game.gameState import GameState
from collections import deque
from datetime import datetime
from game.logger import Logger
import json
from typing import List
import logging


class StoriesGame(StoriesObject):
    """
    Represents a StoriesGame instance
    """


    def __init__(self, installationId:str, genre:str, total_points:int=20, game_id:str=None, game_parameters_type="prod"):
        """
        """
        self._installation_id = installationId
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        self._game_parameters_type = GameParametersType[game_parameters_type.upper()]      # can be "test", "prod", or "custom"
        self._resource_folder = self._env.get_resource_folder()     # base resource folder for example, "/Compile/stories/resources"
        #
        # load game parameters
        #
        self._load_game_configuration()
        
        self._genre = GenreType[genre.upper()]
        self._game_id = game_id
        self._total_points = total_points
        self._game_constants = GameConstants({'edition':'standard'})
        self._start_datetime:datetime = None
        self._end_datetime:datetime = None
        
        self._create_story_decks()    # creates the CardDecks for StoryCards and player discards
        self._deal_size = 10          # max number of cards in a player's hand
        #
        # create & initialize the GameState which includes a list of Players
        #
        self._game_state = GameState(self._game_id, total_points, self._game_parameters_type)
        self.game_duration = 0
        self.round_durations:List[int] = []

              
    def _load_game_configuration(self):
        """Loads the game parameters and occupations JSON files for this edition.
        
        """
        game_params_type = self._game_parameters_type.value
        self._game_parameters_filename = f'{self._resource_folder}/gameParameters_{game_params_type}.json'

        with open(self._game_parameters_filename, "r") as fp:
            jtxt = fp.read()
            self._game_parameters = GameParameters(json.loads(jtxt))
        fp.close()
        
    @property
    def genre(self)->GenreType:
        return self._genre
    
    def _create_story_decks(self, character_aliases:dict=None):
        """Load the story decks for a given genre (story_card_deck)
            Also creates an empty CardDeck for player discards (story_discard_deck)
            Arguments:
                aliases - optional 4-element dict of character aliases
                        This overrides settings in the gameParameters files.
        """
        aliases = self.game_parameters.character_aliases if character_aliases is None else character_aliases
        self._story_card_deck = CardDeck(self.resource_folder, self.genre, aliases=aliases)
        self._story_discard_deck = deque()      # empty deque for discards. Player discards added to the right
        
    def set_character_aliases(self, names:List[str]):
        """Updates story_card_deck with new character alias names
            Arguments:
                names - a List of 4 alias names (str)
        """
        self._story_card_deck.update_character_aliases(names)
        
    def add_to_discard(self, card:StoryCard):
        self._story_discard_deck.append(card)   # add to the right
    
    @property
    def game_parameters(self) -> GameParameters:
        return self._game_parameters
    
    def bypass_error_checks(self)->bool:
        return self.game_parameters.bypass_error_checks
    
    def check_errors(self)->bool:
        """A convenience method that returns True if checking for errors,
            usually after a player's turn, False otherwise.
        """
        return not self.game_parameters.bypass_error_checks
    
    @property
    def game_state(self):
        return self._game_state
    
    @property
    def game_id(self):
        return self._game_id
    
    @property
    def installation_id(self):
        return self.installation_id
    
    @installation_id.setter
    def installation_id(self, value):
        self._installation_id = value

    @property
    def resource_folder(self)->str:
        return self._resource_folder
    
    @property
    def story_card_deck(self)->CardDeck:
        return self._story_card_deck
    
    @property
    def story_discard_deck(self)->deque:
        return self._story_discard_deck
    
    def peek_discard(self)->StoryCard|None:
        """Peeks at the top card if there is one, else None
        """
        return self._story_discard_deck[-1] if len(self._story_discard_deck) > 0 else None
    
    def pop_discard(self)->StoryCard:
        return self._story_discard_deck.pop() if len(self._story_discard_deck) > 0 else None
    
    @property
    def deal_size(self)->int:
        return self._deal_size
    
    @deal_size.setter
    def deal_size(self, value):
        self._deal_size = value
    
    def add_player(self, player:Player):
        """Adds a new Player to the game.
            This also deals deal_size number (typically 10) of story cards to the player
            and sets the reference to this StoriesGame instance in player.my_game
        """
        self.game_state.add_player(player)
        player.my_game = self
        # the game deals new cards to the player
        cards = self._story_card_deck.draw_cards(self.deal_size)
        player.story_card_hand.add_cards(cards)
        player.game_id = self._game_id
        
    def start(self, what:str="game") ->bool:
        """
        Starts the game
        """
        self._start_datetime = datetime.today()
        return True
        
    def end(self, what:str="round")->int:
        """
            Arguments:
                what - "round" ends the current story round for all players and tallies up points.
                       The winner(s) of the round get 5 points, the player(s) who come in second
                       are awarded 3 points, third place player(s) get 1 point. Everyone else gets 0.
                       
                       "game" ends the current round, tallies the points and then finds a winner.
                TODO - tally points & sort players by points using "round_points" game parameter
        """
        self.game_duration = self.game_state.get_elapsed_time()
        return self.game_duration
    
    def draw_card(self, what:str, action_type:ActionType|None) ->tuple :
        """Draw a card from the deck OR from the top of the global discard deck
                what - what to draw or where to draw from:
                       "new" - draw a card from the main card deck
                       "discard" - draw the top of the global discard deck
                       <type> - any of: "title", "opening", "opening/story", "story", "closing", "action"
                action_type - if what == "action", the ActionType to draw: "meanwhile", "trade_lines", "steal_lines",
                        "stir_pot", "draw_new", "change_name"
            Returns:
                A Tuple(StoryCard, str). If StoryCard is None, the str returned is an error message
                 for example if drawing from an empty discard deck
            Note uses game_state.types_to_omit, a List[CardTypes] to omit (not draw)
        """
        types_to_omit = self.game_state.types_to_omit    # possibly empty List[CardType]
        card = None
        message = None
        if what.lower() == 'new':
            card = self.story_card_deck.draw_new(types_to_omit)
        elif what.lower() == 'discard' and len(self._story_discard_deck) > 0:
            #
            # draw the top card from the right side of the discard deque
            #
            card = self.pop_discard()
        elif what in self.story_card_deck.card_types_list:    # "title", "opening", "opening/story", "story", "closing", "action"
            #
            # draw the next occurrence of this CardType
            #
            card_type:CardType = CardType[what.upper()]
            card = self.story_card_deck.draw_type(card_type, action_type)
        else:
            message = f"{what} is an invalid draw option"
        
        if card is None:
            message = f"No cards available for '{what}'"    # card is None
        return card, message
        
    def get_discard(self)->tuple():
        """Peeks at the top card of the game discard pile if there is one, else returns None
        """
        message = None
        card = self._story_discard_deck[-1] if len(self._story_discard_deck) > 0 else None
        if card is not None:
            message = str(card)
        else:
            message = "No discards to draw from"    # card is None
        
        return card, message
    
    def get_cards_by_type(self, card_type:str)->List[str]:
        return self._story_card_deck.get_cards_by_type(card_type)
    
    def get_cards(self)->List[str]:
        """Gets remaining story cards in the order they appear in the story_card_deck (CardDeck)
            Note that remaining cards are the cards not yet drawn by players.
            Output Format for each card is the stringified StoryCard: <ordinal>. <card_type> <card_number> : <text>
            @see StoryCard.__str__()
        """
        indexes = self._story_card_deck.cards_index    # List[int]
        deck_cards = self._story_card_deck.deck_cards
        cards = []
        next_index = self._story_card_deck.next_index
        for i in range(next_index, len(indexes)):
            ind = indexes[next_index]
            story_card = deck_cards[ind]
            cards.append(str(story_card))
            next_index += 1
        return cards
        
    
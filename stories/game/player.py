'''
Created on Dec 8, 2023

@author: don_bacon
'''

from game.storiesObject import StoriesObject
from game.gameConstants import CardType
from game.gameUtils import GameUtils
from game.storyCardHand import StoryCardHand
from game.storyCard import StoryCard
from game.commandResult import CommandResult

from datetime import datetime
from typing import Dict, List
import json

class Player(StoriesObject):
    """
        Represents a Stories game player
    """


    def __init__(self, number=0, name="Player", player_id="", initials="xyz", email="xyz@gmail.com", game_id=None):
        self._player_name = name
        self._player_initials = initials            # unique initials - no player can have the same initials
        self._player_id = player_id
        self._player_email = email
        self._game_id = game_id
        self._number = number       # my player number, values 0 to #players-1
        self._my_game = None        # will be a StoriesGame reference
        self._points = 0
        self._story_card_hand = StoryCardHand()       # this player's story cards in his/her hand and the cards already played
        self._command_history:List[str] = []          # a list of commands executed by a player
        self._num_cards_played = 0      # on this players turn, determines the #cards to discard
        self._num_cards_discarded = 0   # must discard the same number played
        self._card_drawn = False        # set to True when the player draws a card from one of the game decks
        self._story_elements_played = {CardType.TITLE : 0, CardType.OPENING : 0, CardType.STORY : 0, CardType.CLOSING : 0, CardType.ACTION : 0}
    
    @property
    def player_id(self):
        return self._player_id

    @player_id.setter
    def player_id(self, value):
        self._player_id = value

    @property
    def player_email(self) ->str:
        return self._player_email

    @player_email.setter
    def player_email(self, value:str):
        self._player_email = value

    @property
    def player_name(self):
        """Get the player's name."""
        return self._player_name
    
    @player_name.setter
    def player_name(self, value):
        self._player_name = value
        
    @property
    def player_initials(self) ->str:
        return self._player_initials
    
    @player_initials.setter
    def player_initials(self, value:str):
        self._player_initials = value

    @property
    def number(self):
        return self._number
    
    @number.setter
    def number(self, value):
        self._number = value
        
    @property
    def points(self)->int:
        return self._points
    
    @points.setter
    def points(self, value):
        self._points = value

    @property
    def game_id(self)->str:
        return self._game_id
    
    @game_id.setter
    def game_id(self, value):
        self._game_id = value

    @property
    def my_game(self):
        """Returns CareersGame reference
        """
        return self._my_game
    
    @my_game.setter
    def my_game(self, game):
        """Set the value of the player's StoriesGame.
            This is done by the StoriesGame add_player function.
        """
        self._my_game = game
        
    @property
    def num_cards_played(self)->int:
        return self._num_cards_played
    
    @num_cards_played.setter
    def num_cards_played(self, num):
        self._num_cards_played = num
    
    @property
    def num_cards_discarded(self)->int:
        return self._num_cards_discarded
    
    @num_cards_discarded.setter
    def num_cards_discarded(self, num):
        self._num_cards_discarded = num
        
    @property
    def card_drawn(self)->bool:
        return self._card_drawn
    
    @card_drawn.setter
    def card_drawn(self, value:bool):
        self._card_drawn = value
    
    @property
    def story_card_hand(self)->StoryCardHand:
        return self._story_card_hand
    
    @property
    def story_elements_played(self)->Dict[CardType,int]:
        return self._story_elements_played
    
    def add_card(self, card:StoryCard):
        self.story_card_hand.add_card(card)
        
    def size(self)->int:
        """Returns the number of cards in the player's hand
        """
        return self.story_card_hand.hand_size()
    
    def add_command(self, command:str):
        """Adds a command to the player's command_history
        """
        self._command_history.append(command)
        
    def play_card(self, card:int|StoryCard)->StoryCard|None:
        """Plays a single card from the player's hand.
            This assumes the card with the given number is a story element (Title, Opening, Opening/Story, or Closing)
            and or an ActionCard where the story_element property is True (such as a meanwhile ActionCard)
            Arguments:
                card - the number of the card being played OR a StoryCard instance. Cannot be None
            Returns:
                The StoryCard if it exists, otherwise None.
            This functional also updates counts of the type of story element played.
        """
        assert(card is not None)
        card_number = card.number if isinstance(card, StoryCard) else card
        card_played = self.story_card_hand.play_card(card_number)
        
        if card_played is None:
            pass    # error handled by calling function
        
        else:
            card_type = card_played.card_type
            if card_type is CardType.OPENING_STORY:
                # card played as Opening or Story
                # Treat as an OPENING if this player has not yet played an opening card
                # otherwise play as a STORY card.
                open_count = self.story_elements_played[CardType.OPENING]
                story_count = self.story_elements_played[CardType.STORY]
                if open_count == 0:     # treat as OPENING
                    self.story_elements_played[CardType.OPENING] = 1
                else:                   # treat as story body
                    self.story_elements_played[CardType.STORY] = 1 + story_count
            else:
                count = self.story_elements_played[card_type]
                self.story_elements_played[card_type] = 1 + count
                
            self.num_cards_played = self.num_cards_played + 1
        
        return card_played
        
    def remove_card(self, card_number:int)->StoryCard:
        """Remove a single StoryCard from the player's hand
            Arguments:
                card_number - the number of the card in the player's hand to remove
            Returns:
                The StoryCard removed or None if a card with the given number doesn't exist in the player's hand.
        """
        assert(card_number >=0)
        story_card = self.story_card_hand.remove_card(card_number)
        return story_card
        
    def get_card(self, card_number:int)->StoryCard|None:
        story_card = self.story_card_hand.get_card(card_number)
        return story_card
    
    def discard(self, card_number:int)->StoryCard:
        """Discard card as indicated by card_number from a player's hand
            and adds to the game discard deck.
        """
        card_discarded = self.story_card_hand.remove_card(card_number)
        if card_discarded is not None:
            self.num_cards_discarded = self.num_cards_discarded + 1
            
        return card_discarded
        
    def end_turn(self)->CommandResult:
        """Cleanup and check for errors after my turn
        """
        return_code = CommandResult.SUCCESS
        done_flag = False
        if self.card_drawn:
            if self.num_cards_played == 0 and self.num_cards_discarded == 0:
                return_code = CommandResult.ERROR
                message = "You must play at least 1 card or discard 1 card"
            else:
                done_flag = True
                message = "Turn Complete"
                self.num_cards_played = 0
                self.num_cards_discarded = 0
                self.card_drawn = False
        else:   # you must draw a card
            message = "You must draw a card and then either play or discard a card."
            return_code = CommandResult.ERROR
            
        return CommandResult(return_code, message, done_flag)
        
    def info(self):
        return  f' "name" : "{self.player_name}",  "number" : "{self.number}",  "initials" : "{self.player_initials}"'

    def to_dict(self):
        pdict = {"name" : self.player_name, "number" : self.number, "initials" : self.player_initials}
        pdict['game_id'] = self.game_id
        pdict['points'] = self.points
        return pdict

    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=2)

    def _load(self, player_dict:dict):
        """Loads game state player info from a previously saved game
        """
        self.player_name = player_dict["name"]
        self.number = player_dict["number"]
        self.player_initials = player_dict["initials"]
        self.player_id = player_dict["player_id"]
        self.player_email = player_dict["email"]

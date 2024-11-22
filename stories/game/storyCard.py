'''
Created on Dec 9, 2023

@author: don_bacon
'''

from game.gameConstants import GenreType, CardType, ActionType, GameConstants
from game.storiesObject import StoriesObject
import json

class StoryCard(StoriesObject):
    """Encapsulates a single genre story card
    A Story card has a CardType that indicates how it can be used -
    as a Title, Opening, Opening or Story, Story, or Closing -
    and the text. The text consists of 1 or more sentences.
    If the multi_card flag on an action card is True, the player may play an additional story card at the same time.
    The syntax is comma-separated card numbers with the action multi-card appearing first.
    
    A sort_key is created in order to allow sorting a list of StoryCard.
    The sort_key is a combination of the card.number and the CardType in this order:
    CardType.ACTION, CardType.TITLE, CardType.OPENING, CardType.OPENING_STORY, CardType.STORY, CardType.CLOSING
    """


    def __init__(self, genre:GenreType, cardType:CardType, text:str, number, actionType:ActionType=None, min_arguments=0, max_arguments=0, story_element=True):
        '''
        Constructor
        '''
        self._number = number
        self._genre = genre
        self._card_type = cardType
        self._text = text
        self._action_type = actionType
        self._active = True
        self._min_arguments = min_arguments
        self._max_arguments = max_arguments
        self._story_element = story_element
        self._sort_key:int = 1000 * (GameConstants.CARD_TYPES.index(cardType) + 1) + number
    
    @property
    def sort_key(self)->int:
        return self._sort_key
        
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def card_type(self)->CardType:
        return self._card_type
    
    @property
    def number(self)->int:
        return self._number
    
    @number.setter
    def number(self, value):
        self._number = value
    
    @property
    def text(self)->str:
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
    
    @property
    def action_type(self)->ActionType|None:
        return self._action_type
    
    @property
    def active(self)->bool:
        return self._active
    
    @active.setter
    def active(self, state:bool):
        self._active = state
    
    @property
    def min_arguments(self)->int:
        return self._min_arguments
    
    @min_arguments.setter
    def min_arguments(self, value):
        self._min_arguments = value
        
    @property
    def max_arguments(self)->int:
        return self._max_arguments
    
    @max_arguments.setter
    def max_arguments(self, value):
        self._max_arguments = value
        
    @property
    def story_element(self)->bool:
        return self._story_element
    
    @story_element.setter
    def story_element(self, value):
        self._story_element = value
    
    def to_string(self)->str:
        card_text = f"{self.text}"
        return card_text   
    
    def __str__(self)->str:
        card_text = f"{self.card_type.value}:\t{self._number}. {self.text}"
        return card_text
    
    def __repr__(self)->str:    # official string representation
        return self.to_JSON(indent=0)
    
    def to_dict(self):
        pdict = {"genre" : self.genre.value, "number" : self._number, "card_type" : self.card_type.value, "text" : self.text}
        if self.action_type is not None:
            pdict["action_type"] = self.action_type.value
        return pdict

    def to_JSON(self, indent=2):
        d = self.to_dict()
        return json.dumps(self.to_dict(), indent=indent)
        
'''
Created on Dec 9, 2023

@author: don_bacon
'''

from game.storiesObject import StoriesObject
from game.gameConstants import GenreType, CardType, ActionType
import json

class StoryCard(StoriesObject):
    """Encapsulates a single genre story card
    A Story card has a CardType that indicates how it can be used -
    as a Title, Opening, Opening or Story, Story, or Closing -
    and the text. The text consists of 1 or more sentences.
    """


    def __init__(self, genre:GenreType, cardType:CardType, text:str, number, actionType:ActionType=None):
        '''
        Constructor
        '''
        self._number = number
        self._genre = genre
        self._card_type = cardType
        self._text = text
        self._action_type = actionType
        self._active = True
        
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def card_type(self)->CardType:
        return self._card_type
    
    @property
    def number(self)->int:
        return self._number
    
    @property
    def text(self)->str:
        return self._text
    
    @property
    def action_type(self)->ActionType|None:
        return self._action_type
    
    @property
    def active(self)->bool:
        return self._active
    
    @active.setter
    def active(self, state:bool):
        self._active = state
    
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
        return json.dumps(self.to_dict(), indent)
        
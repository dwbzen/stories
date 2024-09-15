'''
Created on Dec 26, 2023

@author: don_bacon
'''

from game.storyCard import StoryCard
from game.storiesObject import StoriesObject
from game.gameConstants import CardType, ActionType
from typing import List, Dict
import json
from collections.abc import Iterator

class StoryCardList(StoriesObject):
    '''
    Encapsulates a List[StoryCard]
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._cards:List[StoryCard] = []    # empty List for now, cards added with add_cards()
    
    def __iter__(self)->Iterator:
        it = iter(self._cards)
        return it
    
    def __getitem__(self, index)->StoryCard|None:
        return self.get(index)
    
    def __len__(self)->int:
        return len(self._cards)
    
    @property
    def cards(self)->List[StoryCard]:
        return self._cards
    
    def size(self)->int:
        return len(self._cards)
    
    def add_cards(self, cards_to_add:List[StoryCard]):
        for card in cards_to_add:
            self._cards.append(card)
    
    def add_card(self, card:StoryCard):
        self._cards.append(card)
    
    def insert_card(self, line_number:int, story_card:StoryCard):
        """Insert a card after a given line number.
        """
        if line_number >= self.size():
            self.add_card(story_card)
        else:
            #
            # create a new List[StoryCard] with the given card
            # after the card at the given line number.
            # 
            self._cards.insert(line_number, story_card)
        
    def discard_cards(self, card_type:CardType|str)->int:
        """Removes all the cards of a given type
            Arguments:
                card_type - the CardType of cards to remove
            Returns: List[StoryCard] of cards removed
        """
        cardtype = card_type if isinstance(card_type, CardType)  else CardType[card_type.upper()]
        cards_removed:List[StoryCard] = []
        #
        # first append cards of this card type to discards
        #
        ncards = 0
        for card in self._cards:
            if card.card_type is cardtype:
                card.active = False     # virtual remove from cards
                cards_removed.append(card)
                ncards += 1             # number of inactive cards
        #
        # remove the inactive cards from cards
        #
        for i in range(ncards):
            ind = self.find_inactive()
            del self._cards[ind]

        return cards_removed
    
    def discard(self, card_number:int)->StoryCard:
        card_ind = self.index_of(card_number)
        card = None
        if card_ind >= 0:
            card = self._cards[card_ind]
            del self._cards[card_ind]
        return card

    def find_card(self, card_number:int)->StoryCard|None:
        return self._cards[self.index_of(card_number)] if self.card_exists(card_number) else None
    
    def find_first(self, card_type:CardType, action_type:ActionType=None)->int:
        """Finds the index of first instance of a given CardType in cards
            and returns its index, or -1 if not found
        """
        ind = 0
        index = -1
        for card in self._cards:
            found = card.card_type is card_type and (action_type is None or card.action_type is action_type)
            if found: 
                index = ind
                break
            else:
                ind+=1
        return index
    
    def find_first_card(self, card_type:CardType, action_type:ActionType=None)->StoryCard|None:
        index = self.find_first(card_type, action_type)
        return self.cards[index] if index >= 0 else None
    
    def find_inactive(self)->int:
        """Finds the index of the first inactive StoryCard in cards,
            or -1 if none found
        """
        ind = 0
        index = -1
        for card in self._cards:
            if not card.active:
                index = ind
                break
            else:
                ind+=1
        return index
    
    def card_exists(self, card_number:int)->bool:
        """Returns True if the designated card exists, false otherwise
        """
        for card in self._cards:
            if card.number == card_number:return True
        return False
    
    def index_of(self, card_number:int)->int:
        """Returns the index of the card with the designated number in the cards list 0<= index < len(cards)
            or -1 if a card with that number does not exist.
        """
        ind = -1
        for i in range(len(self.cards)):
            if card_number == self._cards[i].number:
                ind = i
                break
        return ind
    
    def get(self, index)->StoryCard|None:
        """Gets the StoryCard at a given index.
            Returns:
                the StoryCard or None if the index is invalid or _cards is empty
        """
        ncards = len(self._cards)
        return self._cards[index] if (ncards > 0 and index >= 0 and index < ncards) else None

    def remove(self, index):
        """Removes the card at the given index.
            Raises an IndexError if the index is invalid
        """
        del self._cards[index]
    
    def card_type_counts(self)->Dict[str,int]:
        counts = {}
        for card_type in CardType:
            counts[card_type.value] = 0
            
        for card in self._cards:
            card_type = card.card_type.value
            n = counts[card_type]
            counts.update( {card_type : n+1} )
        return counts
    
    def to_dict(self)->dict:
        """Returns the cards as a Dict
        """
        cards = [x.to_dict() for x in self._cards]
        deck_dict = {"cards" : cards}
        return deck_dict
    
    def to_string(self, numbered:bool=False)->str:
        """
        """
        if self.size() == 0: card_text = ""
        else:
            card_text_list = []
            n = 0
            for card in self._cards:
                if numbered:
                    txt = f"{n}. ({card.card_type.value}) {card.text}" 
                else:
                    txt = card.text
                    
                card_text_list.append(txt)
                n += 1
            card_text = "".join(card_text_list)
        return card_text
    
    def __str__(self)->str:
        card_text = ""
        for card in self._cards:
            card_text = card_text + f"{card}"
        return card_text
    
    def __repr__(self)->str:
        return self.to_JSON(indent=2)
    
    def to_JSON(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent)

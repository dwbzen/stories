'''
Created on Dec 9, 2023

@author: don_bacon
'''
import json
from game.storiesObject import StoriesObject
from game.storyCard import StoryCard
from game.gameUtils import GameUtils
from game.gameConstants import GenreType, GameConstants, CardType, ActionType

from typing import List, Dict

class CardDeck(StoriesObject):
    """Class representing a deck of game cards a player draws or is given.
    
    """

    def __init__(self, genre:GenreType, story_card_template:dict, alias:dict=None):
        '''
        CardDeck constructor
        Arguments:
            genre - the GenreType
            story_card_template - a dict consisting of a story_card_template and all the loaded StoryCards
            alias - character_alias dict or None
        '''
        #
        #
        self._deck = story_card_template
        self._story_card_template = story_card_template
        self._deck_cards:List[StoryCard] =  story_card_template["cards"]    # only the deck StoryCards
        self._card_types_list:List[str] = story_card_template["card_types_list"]
        self._card_types = story_card_template["card_types"]
        self._card_type_counts = {}
        self._commands = story_card_template["commands"]
        self._command_details = story_card_template["command_details"]
        
        #
        # count the cards and CardTypes
        #
        total_count = 0
        for ct in self._card_types:    # List[Dict]  all CardTypes including ActionCards
            count = ct["maximum_count"]
            self._card_type_counts[ct["card_type"]] = count
            total_count += count
        self._ncards = total_count
        #
        # replace character names with alias
        #
        self.character_alias = alias if alias is not None else {}
                
        self._deck_name = genre.value
        self._cards_index = GameUtils.shuffle(self.size())    # returns an empty list if size==0
        self._next_index = 0
        self._next_card_number = self._ncards
    
        
    def shuffle(self) -> List[int]:
        """ Returns a random sample of the integers from 0 to size-1, where size is the #cards in the deck
            @see GameUtils.shuffle()
        """
        self._cards_index = GameUtils.shuffle(self._size)
        
    def size(self)->int:
        """Returns the number of StoryCards in the main deck (deck_cards)
        """
        return len(self._deck_cards)
    
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def next_index(self):
        return self._next_index
    
    @next_index.setter
    def next_index(self, value):
        self._next_index = value
    
    @property
    def cards_index(self):
        return self._cards_index
    
    @cards_index.setter
    def cards_index(self, value):
        self._cards_index = value
    
    @property
    def deck(self)->List[StoryCard]:
        return self._deck
    
    @property
    def deck_name(self):
        return self._deck_name
    
    @property
    def card_types(self) -> List[Dict]:
        return self._card_types

    @property
    def card_types_list(self)->List[str]:
        return self._card_types_list
    
    @property
    def action_types(self)->List[str]:
        return self.deck["action_types_list"]
    
    @property
    def deck_cards(self)->List[StoryCard]:
        return self._deck_cards
    
    @property
    def card_type_counts(self)->Dict[str,int]:
        return self._card_type_counts
    
    @property
    def character_alias(self)->dict:
        return self._character_alias
    
    @character_alias.setter
    def character_alias(self, alias:dict|None):
        self._character_alias = alias
        #
        # replace the names in all the story cards
        #
        if alias is not None:
            for card in self.deck_cards:
                card.text = CardDeck.replace_names(card.text, alias)
    
    def update_character_alias(self, names:List[str]):
        # prior to update, character_alias = {'Michael': 'Don', 'Nick': 'Brian', 'Samantha': 'Cheryl', 'Vivian': 'Beth'} for example
        # characters - ['Michael', 'Nick', 'Samantha', 'Vivian']
        # card.text character names are the character_alias
        characters = self._deck["characters"]
        if len(names) == len(characters):
            alias = {}
            for ind in range(len(names)):
                alias[self.character_alias[characters[ind]]] = names[ind]
            self._character_alias = alias

    def draw(self, omit_type:CardType=None)->StoryCard:
        """Draw a card from the deck. If no cards remaining, re-shuffle and reset the next_index
            Arguments:
                omit_type - if not None, this will omit drawing a story card of that type.
                    For example, if all players have played a Title, we don't want
                    to draw a card of that type. Same with Opening.
            Returns:
                the next StoryCard.
            Inactive StoryCards are skipped. When the last card is drawn,
            the indexes are re-shuffled and the next_index is reset to 0.
        """
        next_card = None
        while next_card is None:
            if self.next_index < self.size():    # draw the next card
                nxt = self._cards_index[self.next_index]
                next_card = self._deck_cards[nxt]
                
                self.next_index = self.next_index + 1
                if (not next_card.active) or ( omit_type is not None and next_card.card_type is omit_type):
                    next_card = None
            else:
                self.next_index = 0
                self.shuffle()
        return next_card
    
    def draw_type(self, card_type:CardType, action_type:ActionType|None) -> StoryCard:
        """Draw a card of a specific type and ActionType if CardType is ACTION.
            This function is intended for testing game play only.
            Arguments:
                card_type - the CardType to draw
                action_type - if type_to_draw is CardType.ACTION, this is the ACTION_TYPE to draw
            Returns:
                The specified StoryCard from the deck, or None if there are no remaining
                cards of this type_to_draw/action_type
            Notes This function does NOT change the value of next_index.
            Also it does check if the drawn card is not active.
        """
        next_card = None
        card = None
        next_index = self.next_index
        next_ind = self._cards_index[next_index]   # start looking through the deck at the next index
        while next_ind < self.size():
            card = self._deck_cards[next_ind]
            if card.active:
                if action_type is not None:
                    if card.card_type is CardType.ACTION:
                        if card.action_type is action_type:
                            next_card = card
                            break
                        else:
                            next_index += 1
                            next_ind = self._cards_index[next_index]
                elif card.card_type is card_type:
                    next_card = card
                    break

            next_index += 1
            next_ind = self._cards_index[next_index]
                
        if next_card is not None:    # remove from the deck by deactivating so it won't be drawn
            next_card.active = False
        return next_card

    def draw_new(self, types_to_omit:List[CardType]=None)->StoryCard:
        """Draw a card from the story card main deck, skipping the optional list of CardType to omit.
            Arguments:
                types_to_omit - if not None, this will omit drawing a story card having a card_type in types_to_omit
                    For example, if all players have played a Title, we don't want
                    to draw a card of that type. Same with Opening.
        """
        next_card:StoryCard = None
        while next_card is None:
            if self.next_index < self.size():    # draw the next card
                nxt = self._cards_index[self.next_index]
                next_card = self._deck_cards[nxt]
                if not next_card.active:    # skip it if not active
                    continue
                self.next_index = self.next_index + 1
                if next_card.card_type in types_to_omit:
                    # keep on drawing until we get a card whose card_type is not one to omit
                    next_card = None
            else:
                self.next_index = 0
                self.shuffle()
                
        return next_card
    
    def draw_cards(self, ncards:int)->List[StoryCard]:
        """Draw cards from this deck.
            Arguments:
                ncards - the number of cards to draw. Must be >0
            Returns:
                List[StoryCard] of cards drawn.
            Note that this function does not check for card types to omit.
        """
        assert(ncards > 0)
        card_list = []
        for i in range(ncards):
            card_list.append(self.draw())
        return card_list
    
    def deal(self, ncards:int)->List[StoryCard]:
        """Deal n-cards for a player
        """
        return self.draw_cards(ncards)
    
    
    @staticmethod
    def replace_names(line:str, aliases:dict)->str:
        """Replace character name(s) with its alias
            Arguments:
                line - a line of text that may or may not reference a character name.
                alias - a dict of character aliases. The len must be 4 (since there are 4 characters)
        """
        newline = line
        if len(aliases) > 0:
            for key in aliases.keys():
                character = key
                alias = aliases[key]
                if character in line:
                    newline = newline.replace(character, alias)
        return newline
    
    def get_cards_by_type(self, card_type:str)->List[str]:
        cards = []
        for story_card in self._deck_cards:
            if story_card.card_type.value.startswith(card_type):
                cards.append(story_card.text)
        return cards
    
    def get_story_cards_by_type(self,  card_type:str)->List[StoryCard]:
        cards = [sc for sc in self._deck_cards if sc.card_type.value.startswith(card_type)]
        return cards
    
    def _find_card_index(self, card_type:CardType, action_type:ActionType)->int:
        card = None
        for ind in range(self.size()):   # story_card in self._deck_cards:
            story_card = self.deck_cards[ind]
            if story_card.card_type is card_type:
                if action_type is None or story_card.action_type is action_type:
                    card = story_card
                    break
                else:
                    continue
        if card is None:    # remove from the deck by deactivating so it won't be drawn
            ind = -1
        return ind
    
    @property
    def commands(self)->List[str]:
        return self._commands
    
    @property
    def command_details(self)->List[dict]:
        return self._command_details
    
    @property
    def next_card_number(self)->int:
        return self._next_card_number
    
    @next_card_number.setter
    def next_card_number(self, num):
        self._next_card_number = num
    
    def to_dict(self):
        cards = [x.to_dict() for x in self.deck_cards]
        deck_dict = {"cards" : cards}
        return deck_dict
    
    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=2)

    
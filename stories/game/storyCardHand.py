'''
Created on Dec 18, 2023

@author: don_bacon
'''
import json
from game.storiesObject import StoriesObject
from game.storyCard import StoryCard
from game.storyCardList import StoryCardList
from typing import List, Dict
from game.gameConstants import CardType

class StoryCardHand(StoriesObject):
    '''
    Represents the story element cards in a player's hand
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self._cards:StoryCardList = StoryCardList()
        self._discards:StoryCardList = StoryCardList()
        self._my_story_cards:StoryCardList = StoryCardList()
    
    @property
    def cards(self) ->StoryCardList:
        """The List of StoryCards in my hand available to play
        """
        return self._cards
    
    @property
    def my_story_cards(self)->StoryCardList:
        """Returns the List of StoryCard played so far in the order played.
        """
        return self._my_story_cards
    
    @property
    def discards(self)->StoryCardList:
        """Cards no longer needed are put here. This is a player's
            private discard pile which is not available to other players.
            Use case: when all players have played a Title card,
            on their next turn they may discard the Title cards they are holding
            and draw new cards.
        """
        return self._discards
    
    def discard_cards(self, card_type:CardType|str)->int:
        """Removes all the cards of a given type from a player's hand
            and appends them to their personal discard pile.
            
            Returns: number of cards removed
        """
        cards_removed = self._cards.discard_cards(card_type)
        for card in cards_removed:
            self._discards.add_card(card)
        return len(cards_removed)
    
    def story_size(self):
        """The number of StoryCards in my current story.
        """
        return self._my_story_cards.size()
    
    def hand_size(self):
        """The number of cards in my hand. These are ready to be played.
        """
        return self._cards.size()
    
    def last_card_played(self)->StoryCard|None:
        """Returns the instance of the StoryCard last played, or None of no cards have been played.
        """
        index = self._my_story_cards.size() - 1
        return self._my_story_cards.get(index)
    
    def add_card(self, card:StoryCard):
        """Add a StoryCard to my hand.
        """
        self._cards.add_card(card)
        
    def add_cards(self, cards:List[StoryCard]):
        for card in cards: self._cards.add_card(card)
        
    def card_type_counts(self)->Dict[str,int]:
        """Returns a Dict[str, int] of card_type counts of cards in _cards (i.e. the player's hand)
        """
        return self._cards.card_type_counts()
    
    def play_card(self, card_number)->StoryCard|None:
        """Plays a selected StoryCard.
            Arguments:
                card_number - the number of the card to play.
            Returns:
                the StoryCard instance selected or None if no card with that number exists
                
            The selected card is removed from the player's hand (self.cards)
            and appended to their story (self.my_story_cards)
            This leaves a deficit in the player's hand so a new card must be
            drawn from the game card deck OR selected from the common discard pile.
        """
        ind = self._cards.index_of(card_number)
        card = None
        if ind >= 0:
            card = self._cards.get(ind)
            self._my_story_cards.add_card(card)
            self._cards.remove(ind)
        return card
    
    def remove_card(self, card_number)->StoryCard|None:
        """Removes a selected StoryCard from the player's hand. This function is used when a player discards
            to the game discard pile.
            Arguments:
                card_number - the number of the card to play.
            Returns:
                the StoryCard instance selected or None if no card with that number exists
                
            The selected card is removed from the player's hand (self.cards)
        """
        ind = self._cards.index_of(card_number)
        card = None
        if ind >= 0:
            card = self._cards.get(ind)
            self._cards.remove(ind)
        return card
        
    
    def to_dict(self)->dict:
        """Returns the cards in a player's hand and story as a Dict
        """
        cards =  self._cards.to_dict()
        story = self.story_so_far()
        deck_dict = {"cards" : cards, "story" : story}
        return deck_dict
    
    def story_so_far(self)->dict:
        """Returns the cards in a player's story cards as a Dict
        """
        return self._my_story_cards.to_dict()
    
    def to_JSON(self, indent=2):
        return json.dumps(self.to_dict(), indent)
    
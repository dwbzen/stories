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
        self._cards:StoryCardList = StoryCardList()             # the cards in my hand
        self._discards:StoryCardList = StoryCardList()
        self._my_story_cards:StoryCardList = StoryCardList()    # the cards in the player's current story
    
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
    
    def sort(self)->StoryCardList:
        """Sorts the cards (in a player's hand) by CardType and number
        """
        scards = self.cards.cards
        scards_sorted = sorted(scards, key=lambda storyCard: storyCard.sort_key)
        return scards_sorted
    
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
    
    def play_card(self, card_number:int, insert_after_line:int=None)->StoryCard|None:
        """Plays a selected StoryCard.
            Arguments:
                card_number - the number of the card to play
                insert_after_line - a line# in the player's current story or None
            Returns:
                the StoryCard instance selected or None if a card with that number doesn't exist
                
            The selected card is removed from the player's hand (self.cards)
            and appended to their story (self.my_story_cards)
            If this leaves a deficit in the player's hand a new card must be
            drawn from the game card deck OR selected from the common discard pile.
            If the card's CardType is a TITLE, OPENING, or CLOSING, this will replace
            an existing story card if one exists.
        """
        ind = self._cards.index_of(card_number)
        card:StoryCard = None
        type_ind = -1
        if ind >= 0:
            card = self._cards.get(ind)    # card in my hand
            if insert_after_line is not None:
                #
                # insert this card after the insert_after_line
                #
                self._my_story_cards.insert_card(insert_after_line+1, card)
            else:
                if card.card_type is CardType.TITLE or card.card_type is CardType.OPENING or card.card_type is CardType.CLOSING:
                    type_ind = self._my_story_cards.find_first(card.card_type)
                    if type_ind >= 0:
                        # replace the new card in the story
                        current_card:StoryCard  = self._my_story_cards[type_ind]
                        self._my_story_cards.cards[type_ind] = card
                        self.discards.add_card(current_card)
                        self.remove_card(current_card.number)
                        return card
                if card.story_element:
                    self._my_story_cards.add_card(card)
                self._cards.remove(ind)
        return card
    
    def get_card(self, card_number:str|int)->StoryCard|None:
        """Gets the selected StoryCard from a player's hand.
            Arguments:
                card_number - the number of the card to get.
            Returns:
                the StoryCard instance selected or None if no card with that number exists
        """
        ind = self._cards.index_of(int(card_number))
        card = None
        if ind >= 0:
            card = self._cards.get(ind)
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
    
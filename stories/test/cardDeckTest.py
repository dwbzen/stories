'''
Created on Dec 20, 2023

@author: don_bacon
'''

import unittest
from game.cardDeck import CardDeck
from game.storyCardHand import StoryCardHand
from game.gameConstants import GenreType, CardType, ActionType

class CardDeckTest(unittest.TestCase):
    '''
    classdocs
    '''
        
    def setUp(self):
        print("\nSetUp the next test")
        unittest.TestCase.setUp(self)
        resource_folder = "/Users/dwbze/OneDrive/Documents/Compile/stories/resources"
        self.card_deck = CardDeck(resource_folder, GenreType.HORROR)
        print(f"#cards: {self.card_deck.size()}")
        print(self.card_deck.card_type_counts)
        self.story_card_hand = StoryCardHand()
        self.deal_size = 10     # number of cards to deal
        self.deal_cards()       # needed for subsequent tests
    
    def deal_cards(self):
        cards = self.card_deck.deal(self.deal_size)
        self.story_card_hand.add_cards(cards)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        # nothing to tear down

    def test_count_card_types(self):
        print("\ntest_count_card_types ===================")
        counts = self.story_card_hand.card_type_counts()
        print(counts)
    
    def test_discards(self):
        print("\ntest_discards ===========================")
        # remove Title cards
        ncards = self.story_card_hand.discard_cards(CardType.TITLE)
        print(f"{ncards} Title cards removed")
        counts = self.story_card_hand.card_type_counts()
        print(counts) 
        
    def test_list_cards(self):
        #
        # tests the StoryCardList iterator
        #
        print("\ntest_list_cards ==========================")
        for card in self.story_card_hand.cards:
            card_type = card.card_type.value
            text = card.text
            print(f"{card.number}. {card_type}\n{text}")
        itr = self.story_card_hand.cards.__iter__()
        print(type(itr))
        print("Test Complete")
        
    def test_draw_omit_title(self):
        print("\ntest_draw_omit_title ====================")
        ncards = self.story_card_hand.discard_cards(CardType.TITLE)
        counts = self.story_card_hand.card_type_counts()
        print(f"{ncards} Title cards removed")
        print(f"  {counts}")
        self.assertEqual(counts["Title"], 0)
        
        for n in range(ncards):    # draw replacements for the removed Title cards
            next_card = self.card_deck.draw(omit_type=CardType.TITLE)
            self.assertFalse(next_card is None)
            self.assertFalse(next_card.card_type is CardType.TITLE)
            self.story_card_hand.add_card(next_card)
    
        ncards = self.story_card_hand.hand_size()
        self.assertEqual(ncards, self.deal_size)
        counts = self.story_card_hand.card_type_counts()
        self.assertEqual(counts["Title"], 0)
        print(f"  {counts}")
    
    def test_draw_type(self):
        #
        # draw a specific CardType and ActionType
        #
        print("\ntest_draw_type ==========================")
        action_type = None
        for card_type in list(CardType):
            story_card = self.card_deck.draw_type(card_type, action_type)
            self.assertTrue(story_card.card_type is card_type)
        card_type = CardType.ACTION
        for action_type in list(ActionType):
            story_card = self.card_deck.draw_type(card_type, action_type)
            self.assertTrue(story_card.action_type is action_type)
        
    @unittest.skip("test_player_draw")
    def test_player_draw(self):
        print("interactive test_player_draw ==============")
        for i in range(self.deal_size):
            story_card = self.card_deck.draw()
            card_type = story_card.card_type.value
            text = story_card.text
            print(f"{story_card.number}. {card_type}\n{text}")
        while True:
            cmd = input("Command: ")
            if cmd=='end':
                break
            else:
                story_card = self.card_deck.draw()
                print(f"{story_card.number}. {story_card.card_type.value}\n{story_card.text}")
  
if __name__ == '__main__':
    unittest.main()
    
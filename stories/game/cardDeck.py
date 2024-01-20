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

    def __init__(self, resource_folder, genre:GenreType, load_deck=True, aliases:dict=None):
        '''
        CardDeck constructor
        Arguments:
            resorce_folder - base resource folder for example, "/Compile/stories/resources"
            genre - the GenreType
        '''
        self._resource_folder = resource_folder
        self._template_filename = f"{resource_folder}/story_cards_template.json"
        self._genre = genre
        self._character_aliases:dict = aliases if aliases is not None else {}
        self._genres_folder = f"{self._resource_folder}/genres/{genre.value}"   # for example "/Compile/stories/resources/genres/horror"
        #
        # load the story template file and genre resources
        # to create the deck of Storycards
        #
        self._deck:Dict = self.load_template_file(genre)
        self._deck_cards:List[StoryCard] = []    # only the deck StoryCards
        self._ncards = self.load_cards(self._deck, resource_folder, genre) if load_deck else 0
        #
        # replace character names with aliases
        #
        self.character_aliases = aliases
        
        self._deck_name = genre.value
        self._card_types = []
        self._card_type_counts = {}

        self._cards_index = GameUtils.shuffle(self.size())    # returns an empty list if size==0
        self._next_index = 0
    
        
    def shuffle(self):
        self._cards_index = GameUtils.shuffle(self._size)
        
    def size(self):
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
    def deck_cards(self)->List[StoryCard]:
        return self._deck_cards
    
    @property
    def card_type_counts(self)->Dict[str,int]:
        return self._card_type_counts
    
    @property
    def character_aliases(self)->dict:
        return self._character_aliases
    
    @character_aliases.setter
    def character_aliases(self, aliases:dict|None):
        self._character_aliases = aliases
        #
        # replace the names in all the story cards
        #
        if aliases is not None:
            for card in self.deck_cards:
                card.text = CardDeck.replace_names(card.text, aliases)
    
    def update_character_aliases(self, names:List[str]):
        # prior to update, character_aliases = {'Michael': 'Don', 'Nick': 'Brian', 'Samantha': 'Cheryl', 'Vivian': 'Beth'} for example
        # characters - ['Michael', 'Nick', 'Samantha', 'Vivian']
        # card.text character names are the character_aliases
        characters = self._deck["characters"]
        if len(names) == len(characters):
            aliases = {}
            for ind in range(len(names)):
                aliases[self.character_aliases[characters[ind]]] = names[ind]
            self.character_aliases = aliases

    def draw(self, omit_type:CardType=None)->StoryCard:
        """Draw a card from the deck. If no cards remaining, re-shuffle and reset the next_index
            Arguments:
                omit_type - if not None, this will omit drawing a story card of that type.
                    For example, if all players have played a Title, we don't want
                    to draw a card of that type. Same with Opening.
        
        """
        next_card = None
        while next_card is None:
            if self.next_index < self.size():    # draw the next card
                nxt = self._cards_index[self.next_index]
                next_card = self._deck_cards[nxt]
                self.next_index = self.next_index + 1
                if omit_type is not None and next_card.card_type is omit_type:
                    next_card = None
            else:
                self.next_index = 0
                self.shuffle()
        return next_card
    
    def draw_new(self, types_to_omit:List[CardType]=None)->StoryCard:
        """Draw a card from the story card main deck, skipping the optional list of CardType to omit.
            Arguments:
                types_to_omit - if not None, this will omit drawing a story card having a card_type in types_to_omit
                    For example, if all players have played a Title, we don't want
                    to draw a card of that type. Same with Opening.
        """
        next_card = None
        while next_card is None:
            if self.next_index < self.size():    # draw the next card
                nxt = self._cards_index[self.next_index]
                next_card = self._deck_cards[nxt]
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
    
    def load_template_file(self, genre:GenreType):
        with open(self._template_filename, "r") as fp:
            jtxt = fp.read()
            template = json.loads(jtxt)    # returns a Dict
        fp.close()
        deck = { "Help" : f"{genre.value} story card deck"}
        deck["card_types_list"] = template["card_types_list"]
        deck["action_types_list"] = template["action_types_list"]
        deck["card_types"] = template["card_types"]
        deck["action_types"] = template["action_types"]
        deck["characters"] = template["characters"]
        self._card_types = deck["card_types"]
        self._card_type_counts = {}
        for c in self._card_types:    # dict
            card_type = c["card_type"]
            max_count = c["maximum_count"]
            self._card_type_counts[card_type] = max_count
            
        return deck
    
    def load_cards(self, deck:dict, resource_folder, genre:GenreType)->int:
        """Loads the specified card deck text files.
            Arguments:
                path -  resource file path
                genre - the GenreType to load
            Returns:
                the number of StoryCards added
            Also sets the values of _deck, _deck_cards, _card_types
            if character_aliases is not an empty dictionary, character names
            in each line is replaced by its alias.
        """
        filenames = GameConstants.get_genre_filenames(genre)   # Dict with CardType as the key and the card text file as the value
        total_count = 0
        number = 0
        for card_type in filenames.keys():
            filepath = f"{resource_folder}/genres/{genre.value}/{filenames[card_type]}"
            count = 0
            max_count = self._card_type_counts[card_type.value]
            with open(filepath) as fp:
                lines =  fp.readlines()
                #
                # create a random list max_count long so every game is different
                #
                nlines = len(lines)
                line_indexes = GameUtils.shuffle(nlines)
                for ind in range(nlines):
                    line = lines[line_indexes[ind]]
                    if len(line) == 0 or line.startswith("--"):    # skip blank and comment lines
                        continue
                    #
                    # replace character names with aliases
                    #
                    #line = CardDeck.replace_names(line, self._character_aliases)
                    #
                    # create a StoryCard instance for this card type
                    #
                    storyCard = StoryCard(genre, card_type, line, number)
                    self._deck_cards.append(storyCard)
                    number+=1
                    count+=1
                    if count >= max_count:
                        break
                fp.close()
            self._card_type_counts[card_type.value] = count
            total_count += count
        #
        # add the action cards
        #
        count = 0
        card_type = CardType.ACTION
        for action in deck["action_types"]:
            action_type = ActionType[action["action_type"].upper()]
            text = f'{action["text"]}\n'
            qty = action["quantity"]
            multi_card = action.get("multi_card", 0)==1
            for i in range(qty):
                storyCard = StoryCard(genre, card_type, text, number, action_type, multi_card)
                self._deck_cards.append(storyCard)
                number+=1
            count += qty
        self._card_type_counts[card_type.value] = count

        deck["cards"] = self._deck_cards
        return len(self._deck_cards)
    
    @staticmethod
    def replace_names(line:str, aliases:dict)->str:
        """Replace character name(s) with its alias
            Arguments:
                line - a line of text that may or may not reference a character name.
                aliases - a dict of character aliases. The len must be 4 (since there are 4 characters)
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
    
    def to_dict(self):
        cards = [x.to_dict() for x in self.deck_cards]
        deck_dict = {"cards" : cards}
        return deck_dict
    
    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=2)

    
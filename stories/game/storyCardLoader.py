'''
Created on Aug 20, 2024

@author: don_bacon
'''

from game.gameConstants import GenreType, GameConstants, CardType, ActionType
import json
import pymongo
from typing import Dict, List
from game.storyCard import StoryCard
from game.gameParameters import GameParameters
from game.gameUtils import GameUtils
from game.commandResult import CommandResult

class StoryCardLoader(object):
    '''
    Loads the story cards for a given genre from text files
    or the MongoDB genres database
    '''


    def __init__(self, source:str, genre:GenreType, game_parameters:GameParameters, resource_folder:str, story_card_template:dict):
        '''
        Constructor
        '''
        self._resource_folder = resource_folder
        self._genre = genre
        self._source = source
        self._genres_folder = f"{self._resource_folder}/genres/{genre.value}"   # for example "/Compile/stories/resources/genres/horror"
        #
        #
        self._story_card_template = story_card_template
        self._game_parameters = game_parameters

        self._deck_cards:List[StoryCard] = []       # only the deck StoryCards
        
        self._deck_name = genre.value
        self._deck = self.initialize_story_card_deck()
        
    def initialize_story_card_deck(self):
        deck = { "Help" : f"{self.genre.value} story card deck"}
        deck["card_types_list"] = self.story_card_template["card_types_list"]   # "Title", "Opening", "Opening/Story", "Story", "Closing"
        self._card_types_list = []
        #
        # convert the card types to lower case for use in commands
        # "title", "opening", "opening/story", "story", "closing", "action"
        #
        for ct in deck["card_types_list"]:
            self._card_types_list.append(ct.lower())
            
        deck["action_types_list"] = self.story_card_template["action_types_list"]
        deck["card_types"] = self.story_card_template["card_types"]
        deck["action_types"] = self.story_card_template["action_types"]
        deck["characters"] = self.story_card_template["characters"]
        
        self._card_types = deck["card_types"]
        self._card_type_counts = {}
        for c in self._card_types:    # dict
            card_type = c["card_type"]
            max_count = c["maximum_count"]
            self._card_type_counts[card_type] = max_count

        return deck
    
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def story_card_template(self)->dict:
        return self._story_card_template
    
    @property
    def resource_folder(self)->str:
        return self._resource_folder
    
    @property
    def deck_cards(self)->List[StoryCard]:
        return self._deck_cards
    
    @property
    def game_parameters(self)->GameParameters:
        return self._game_parameters

    @property
    def deck_name(self):
        return self._deck_name

    @property
    def deck(self)->List[StoryCard]:
        return self._deck
 
    @property
    def card_types(self) -> List[Dict]:
        return self._card_types

    @property
    def card_types_list(self)->List[str]:
        return self._card_types_list

    def size(self)->int:
        return len(self._deck_cards)
           
    def load_cards(self)->List[StoryCard]:
        """Loads the specified card deck text files.
            Properties used:
                story_card_template - the story card template Dict
                resource_folder -  resource file path
                genre - the GenreType to load
                game_parameters - character_alias and DB_NAME_GENRES
            Returns a List[StoryCard]

            Also sets the values of _deck, _deck_cards, _card_types
            if character_alias is not an empty dictionary, character names in each line is replaced by its alias.
            The "card_types" element in story_card_template.json gives the number of cards to load for each card_type.
            This number is <= the number of lines in the file.
            ActionCards are instanced from action_types in the story card template.
            The entire file is shuffled so that the selection is unique for each game.
            @see stories.game.GameUtils
        """
        result = self.load_cards_db() if self._source == 'mongo' else self.load_cards_text()
        result.message = f"{len(self._deck_cards)} cards loaded"
        return result
    
    def load_cards_db(self):
        """Loads game story cards from MongoDB 'genres' database
            Arguments:
            Returns CommandResult
            The list of StoryCard returned in self._deck_cards
        """
        db_url = self.game_parameters.db_url
        db_name = self.game_parameters.db_name_genres
        result = CommandResult(CommandResult.SUCCESS)
        try:
            mongo_client = pymongo.MongoClient(db_url)
            genres_db = mongo_client[db_name]

        except Exception as ex:
            message = f'MongoDB error, exception: {str(ex)}'
            result.message = message
            result.return_code = CommandResult.ERROR
            return result
        
        collection = genres_db[self.genre.value]
        total_count = 0
        number = 0
        for ct in CardType:
            max_count = self._card_type_counts[ct.value]
            query = {"cardType":ct.value}
            docs = collection.find_one(query)
            if docs is not None:
                carddocs = docs["cards"]    # dict line:int, content:str
                count = 0
                lines = []
                for cd in carddocs:
                    content = cd["content"] + "\n"
                    lines.append(content)
                lines = GameUtils.shuffle_list(lines)
                for line in lines:
                    story_card = StoryCard(self.genre, ct, line, number)
                    self._deck_cards.append(story_card)
                    number+=1
                    count+=1
                    if count >= max_count:
                        break
                total_count += count
                
        action_cards_count = self.load_action_cards(number)
        total_count += action_cards_count
        result.properties = {"count" : total_count}
                
        return result
    
    def load_cards_text(self)->CommandResult:
        """Loads game story cards from genre text files.
            Arguments:
            Returns CommandResult
            The list of StoryCard returned in self._deck_cards
        """
        filenames = GameConstants.get_genre_filenames(self.genre)   # Dict with CardType as the key and the card text file as the value
        total_count = 0
        number = 0
        lines = []
        result = CommandResult(CommandResult.SUCCESS)
        for card_type in filenames.keys():
            filepath = f"{self.resource_folder}/genres/{self.genre.value}/{filenames[card_type]}"
            count = 0
            max_count = self._card_type_counts[card_type.value]
            # print(filepath)
            lines = self.read_story_file(filepath, shuffle=True)
            #
            # create a random list max_count long so every game is unique
            #
            for line in lines:
                #
                # create a StoryCard instance for this card type
                #
                storyCard = StoryCard(self.genre, card_type, line, number)
                self._deck_cards.append(storyCard)
                number+=1
                count+=1
                if count >= max_count:
                    break
                
            self._card_type_counts[card_type.value] = count
            total_count += count
            
        action_cards_count = self.load_action_cards(number)
        total_count += action_cards_count
        result.properties = {"count" : total_count}
        return result
    
    def load_action_cards(self, number)->int:
        #
        # add the action cards
        #
        count = 0
        card_type = CardType.ACTION
        for action in self.story_card_template["action_types"]:
            action_type = ActionType[action["action_type"].upper()]
            text = f'{action["text"]}\n'
            qty = action["quantity"]
            max_arguments = action.get("max_arguments", 0)
            min_arguments = action.get("min_arguments", 0)
            story_element = action.get("story_element", 0)==1
            for i in range(qty):
                storyCard = StoryCard(self.genre, card_type, text, number, action_type, min_arguments, max_arguments, story_element)
                self._deck_cards.append(storyCard)
                number+=1
            count += qty
        self._card_type_counts[card_type.value] = count
        
        return count

    def read_story_file(self, filepath, shuffle=False)->List[str]:
        with open(filepath) as fp:
            lines = []
            continue_line = False
            cline = ""
            for line in fp:
                line = line.lstrip().rstrip()    # delete left padding and trailing \n
                if line=="" or line.startswith("--"):    # skip comment lines
                    continue
                if line.endswith('\\'):    # continues on next line
                    line = line.removesuffix('\\')
                    if continue_line:
                        cline = f"{cline}\n{line}"
                    else:
                        continue_line = True
                        cline = line
                else:
                    if continue_line:
                        cline = f"{cline}\n{line}\n"
                        lines.append(cline)
                        continue_line = False
                    else:
                        lines.append(f"{line}\n")
        fp.close()
        if shuffle:
            lines = GameUtils.shuffle_list(lines)
        return lines
    
if __name__ == '__main__':
    """A quick test to load a parameters file, story card template, and story cards.
    """
    print("Done")
    
    
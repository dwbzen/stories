'''
Created on Jul 9, 2024

@author: don_bacon
'''
import unittest
from game.gameConstants import GenreType, CardType
from game.environment import Environment
from game.chatManager import ChatManager
from game.commandResult import CommandResult

class ChatManagerTest(unittest.TestCase):

    def setUp(self):
        print("\nSetUp the next test")
        unittest.TestCase.setUp(self)
        self._env = Environment.get_environment()
        self._resource_folder = self._env.get_resource_folder()     # base resource folder
        
    def testLoadChatFiles(self):
        chat_manager = ChatManager(self._resource_folder, GenreType.HORROR)
        result:CommandResult = chat_manager.load_chat_files()
        self.assertTrue(result.return_code is CommandResult.SUCCESS)
        print(f"load result: {result.return_code}\message: {result.message}")
        print(f"system text: {chat_manager.system_text}")
        for card_type in [CardType.TITLE, CardType.OPENING, CardType.STORY, CardType.CLOSING]:
            txt = chat_manager.get_user_text(card_type)
            print(f"{card_type.value}:\n{txt}")
            
    def test_OpenAI_API(self):
        chat_manager = ChatManager(self._resource_folder, GenreType.HORROR)
        result:CommandResult = chat_manager.load_chat_files()
        self.assertTrue(result.return_code is CommandResult.SUCCESS)
        system_text = chat_manager.system_text
        user_text = chat_manager.get_user_text(CardType.STORY)
        completion = chat_manager.create_completion(system_text, user_text)
        print(completion)
        

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        # nothing to tear down

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
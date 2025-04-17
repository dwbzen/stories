'''
Created on December 13, 2023

@author: don_bacon
'''

from game.environment import Environment
import logging

# deprecated
class Logger(object):
    '''
    Global gateway to message logging
    '''
    logger = logging.getLogger(__name__)
    
    def __init__(self, game_id, logfile_path, level=logging.INFO):
        '''
        Initialize logging configuration
        '''
        self.game_id = game_id
        
        self._logfile_path = logfile_path
        
        self._dataRoot = Environment.get_environment().package_base

        logging.basicConfig(filename=self._logfile_path, encoding='utf-8', level=level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
        Logger.logger.debug(f"Logging configured successfully for {game_id}, level {level} ")
        

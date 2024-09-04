from __future__ import absolute_import  # multi-line and relative/absolute imports

from .__version__ import __title__, __description__, __version__
from .__version__ import __author__, __author_email__, __license__
from .__version__ import __copyright__


__all__ = [
    'gameManager',
    'playerManager',
    'historyManager'
]

from .gameManager import StoriesGameManager, Game, GameInfo
from .playerManager import StoriesPlayer, StoriesPlayerManager
from .historyManager import HistoryManager, PlayerGameHistory

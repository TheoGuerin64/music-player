from typing import Type

from .admin import Admin
from .bot_cog import BotCog
from .events import Events
from .music import Music
from .one_piece import OnePiece
from .space import Space
from .trivia import Trivia

COGS: list[Type[BotCog]] = [Admin, Events, Music, OnePiece, Space, Trivia]

from music_player.bot import MyBot
from music_player.settings import DISCORD_TOKEN


def main() -> None:
    MyBot().run(DISCORD_TOKEN)

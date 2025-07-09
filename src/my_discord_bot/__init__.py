from my_discord_bot.bot import MyBot
from my_discord_bot.settings import DISCORD_TOKEN


def main() -> None:
    MyBot().run(DISCORD_TOKEN)

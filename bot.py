import logging
import os
import signal
import sys

import discord
from discord.ext import commands

from settings import TOKEN

logger = logging.getLogger("discord")


class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix=(),
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="/help"
            )
        )

    async def load_extension(self, name: str, *, package: str | None = None) -> None:
        """Override load_extension to log errors."""
        try:
            await super().load_extension(name, package=package)
        except commands.ExtensionError as error:
            logger.error("Failed to load extension %s: %s", name, error)

    async def setup_hook(self) -> None:
        """Override setup_hook to load extensions."""
        for file in os.listdir("./extensions"):
            if not file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
        logger.info("Extensions loaded.")

    async def on_ready(self) -> None:
        """Override on_ready to log when the bot is ready."""
        assert self.user is not None
        logger.info("Logged in as %s", self.user.name)

    async def close(self) -> None:
        """Override close to log when the bot is closed."""
        await super().close()
        logger.info("Bot closed.")


bot = MyBot()
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
bot.run(TOKEN)

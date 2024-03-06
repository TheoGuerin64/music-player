import logging
import os

import discord
from discord.ext import commands

from settings import TOKEN

logger = logging.getLogger("discord")


class Bot(commands.Bot):
    """Custom bot class to load extensions and log errors."""

    def __init__(self):
        super().__init__(
            intents=discord.Intents.all(),
            command_prefix=(),
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="/help"
            )
        )

    async def load_extension(self, name):
        """Override load_extension to log errors."""
        try:
            super().load_extension(name)
        except commands.ExtensionError as error:
            logger.error("Failed to load extension %s: %s", name, error)

    async def setup_hook(self):
        """Override setup_hook to load extensions."""
        for file in os.listdir("./extensions"):
            if not file.endswith(".py"):
                self.load_extension(f"cogs.{file[:-3]}")
        logger.info("Extensions loaded.")

    async def on_ready(self):
        """Override on_ready to log when the bot is ready."""
        logger.info("Logged in as %s", self.user.name)


Bot().run(TOKEN)

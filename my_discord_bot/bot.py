import logging

from discord import Activity, ActivityType, Intents, Interaction
from discord.app_commands import AppCommandError
from discord.app_commands.errors import CommandInvokeError
from discord.ext import commands

from .cogs import COGS
from .exceptions import CommandError

logger = logging.getLogger("discord")


class MyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            intents=Intents.all(),
            command_prefix=(),
            activity=Activity(type=ActivityType.playing, name="/play"),
        )

    async def setup_hook(self) -> None:
        for Cog in COGS:
            try:
                await self.add_cog(Cog(self))
            except Exception as e:
                logger.error(f"Failed to load cog: {e}")
        logger.info("Cogs loaded.")

        if not __debug__:
            await self.tree.sync()
            logger.info("Tree synced.")

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info(f"Logged in as {self.user.name}")

    @staticmethod
    async def on_error(interaction: Interaction, error: AppCommandError) -> None:
        if interaction.response.is_done():
            send = interaction.followup.send
        else:
            send = interaction.response.send_message

        if not isinstance(error, CommandInvokeError) or not isinstance(
            error.original, CommandError
        ):
            await send("An error occurred.")
            logger.error(error, exc_info=True)
            return

        await send(error.original.message, ephemeral=error.original.ephemeral)

import logging

from discord import Interaction, app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


async def on_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
    if interaction.response.is_done():
        send = interaction.followup.send
    else:
        send = interaction.response.send_message
    if isinstance(error, app_commands.errors.AppCommandError):
        await send(str(error))
        logger.error(error)
    else:
        await send("An error occurred.")
        logger.error(error, exc_info=True)


async def setup(bot: commands.Bot) -> None:
    bot.tree.on_error = on_error

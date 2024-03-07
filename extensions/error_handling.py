import logging

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        bot.tree.on_error = self.on_error

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if interaction.response.is_done():
            send = interaction.followup.send
        else:
            send = interaction.response.send_message
        await send("An error occurred.", ephemeral=True)
        logger.error(error, exc_info=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ErrorHandler(bot))

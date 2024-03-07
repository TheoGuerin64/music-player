from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from db import db


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def sync(self, interaction: Interaction):
        """Sync the bot."""
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self.bot.tree.sync()
        await interaction.followup.send("Synced.")

    @app_commands.command()
    @app_commands.describe()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def clear(self, interaction: Interaction, number: int) -> None:
        """Clear messages.

        Args:
            number: The number of messages to delete.
        """
        if interaction.channel is None or not hasattr(interaction.channel, "purge"):
            await interaction.response.send_message("This command can not be used here.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        deleted = await interaction.channel.purge(limit=number, reason="Clear command.")  # type: ignore
        await interaction.followup.send(f"{len(deleted)} message(s) deleted.")

    @app_commands.command()
    @app_commands.describe()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def set_welcome_channel(self, interaction: Interaction, channel: Optional[discord.TextChannel]) -> None:
        """Set the welcome channel.

        Args:
            channel: The welcome channel.
        """
        if interaction.guild is None:
            await interaction.response.send_message("This command can not be used here.", ephemeral=True)
            return

        if channel is None:
            db.set_welcome_channel_id(interaction.guild.id, None)
            await interaction.response.send_message("Welcome channel removed.", ephemeral=True)
        else:
            db.set_welcome_channel_id(interaction.guild.id, channel.id)
            await interaction.response.send_message(f"Welcome channel set to {channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))

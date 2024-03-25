from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from db import db
from error import CommandError


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def sync(self, interaction: Interaction) -> None:
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
            raise CommandError("This command can not be used here.", True)

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
            raise CommandError("This command can not be used here.", True)

        if channel is None:
            db.set_welcome_channel_id(interaction.guild.id, None)
            await interaction.response.send_message("Welcome channel removed.", ephemeral=True)
        else:
            db.set_welcome_channel_id(interaction.guild.id, channel.id)
            await interaction.response.send_message(f"Welcome channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def set_one_piece_channel(self, interaction: Interaction, channel: Optional[discord.TextChannel]) -> None:
        """Set the One Piece channel.

        Args:
            channel: The One Piece channel.
        """
        if interaction.guild is None:
            raise CommandError("This command can not be used here.", True)

        if channel is None:
            db.set_one_piece_channel_id(interaction.guild.id, None)
            await interaction.response.send_message("One Piece channel removed.", ephemeral=True)
        else:
            db.set_one_piece_channel_id(interaction.guild.id, channel.id)
            await interaction.response.send_message(f"One Piece channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def write(self, interaction: Interaction, message: str, channel: Optional[discord.TextChannel]) -> None:
        """Write a message in a channel.

        Args:
            Message: The message to write.
            channel: The channel.
        """
        if interaction.guild is None:
            raise CommandError("This command can not be used here.", True)
        if not isinstance(interaction.channel, discord.TextChannel):
            raise CommandError("This command can not be used here.", True)

        if not channel:
            channel = interaction.channel

        await interaction.response.defer(thinking=True, ephemeral=True)
        await channel.send(message)
        await interaction.followup.send("Message sent.")

    @app_commands.command()
    @app_commands.describe()
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def add_reaction(self, interaction: Interaction, message_id: str, emoji: str) -> None:
        """Add a reaction to a message.

        Args:
            message_id: The message id.
            emoji: The emoji.
        """
        if interaction.guild is None:
            raise CommandError("This command can not be used here.", True)
        if not isinstance(interaction.channel, discord.TextChannel):
            raise CommandError("This command can not be used here.", True)

        if len(message_id) > 20:
            raise CommandError("Invalid message id.", True)
        try:
            message_id_int = int(message_id)
        except ValueError:
            raise CommandError("Invalid message id.", True)

        message = await interaction.channel.fetch_message(message_id_int)
        if not message:
            raise CommandError("Message not found.", True)

        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            await message.add_reaction(emoji)
        except (discord.HTTPException, discord.NotFound, TypeError):
            raise CommandError("Invalid emoji.", True)
        await interaction.followup.send("Reaction added.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))

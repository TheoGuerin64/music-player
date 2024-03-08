from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands


class Music(commands.Cog):
    def __init__(self) -> None:
        super().__init__()

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def join(self, interaction: Interaction, channel: Optional[discord.VoiceChannel]) -> None:
        """Join the voice channel.

        Args:
            channel: Voice channel to join. If not provided, joins the channel of the user who invoked the command.
        """
        if not channel:
            assert isinstance(interaction.user, discord.Member)
            if interaction.user.voice is None or interaction.user.voice.channel is None:
                raise app_commands.AppCommandError("You are not connected to a voice channel.")
            if not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
                raise app_commands.AppCommandError("You are not connected to a voice channel.")
            channel = interaction.user.voice.channel

        await channel.connect()
        await interaction.response.send_message(f"Joined {channel.name}", ephemeral=True)

    @app_commands.command()
    @app_commands.guild_only()
    async def stop(self, interaction: Interaction) -> None:
        """Stop the music and leave the voice channel."""
        if interaction.guild is None:
            raise app_commands.AppCommandError("This command must be used in a guild.")
        if interaction.guild.voice_client is None:
            raise app_commands.AppCommandError("Not connected to a voice channel.")

        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message("Disconnected", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music())

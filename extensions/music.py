import asyncio
import logging
from asyncio import AbstractEventLoop
from typing import Optional

import discord
import youtube_dl
from discord import Interaction, app_commands
from discord.ext import commands

from error import CommandError

youtube_dl.utils.bug_reports_message = lambda: ""

YTDL_FORMAT_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

logger = logging.getLogger(__name__)


class YTDLSource(discord.PCMVolumeTransformer):
    ytdl = youtube_dl.YoutubeDL(YTDL_FORMAT_OPTIONS)

    def __init__(self, source, *, data: dict, volume: float = 0.5) -> None:
        super().__init__(source, volume)
        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_query(cls, query: str, *, loop: Optional[AbstractEventLoop] = None) -> "YTDLSource":
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(query, download=False))

        assert isinstance(data, dict)
        if "entries" in data:
            data = data["entries"][0]

        return cls(discord.FFmpegPCMAudio(data["url"], options="-vn"), data=data)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

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
            if interaction.user.voice is None or not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
                raise CommandError("You are not connected to a voice channel.", True)
            channel = interaction.user.voice.channel

        await interaction.response.defer(ephemeral=True)
        await channel.connect(timeout=10)
        await interaction.followup.send(f"Joined {channel.name}", ephemeral=True)

    @app_commands.command()
    @app_commands.guild_only()
    async def stop(self, interaction: Interaction) -> None:
        """Stop the music and leave the voice channel."""
        assert interaction.guild is not None
        if interaction.guild.voice_client is None:
            raise CommandError("Bot is not connected to a voice channel.", True)

        await interaction.guild.voice_client.disconnect(force=True)
        await interaction.response.send_message("Disconnected", ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def volume(self, interaction: Interaction, volume: int) -> None:
        """Change the player volume.

        Args:
            volume: Volume to set.
        """
        if volume < 0 or volume > 100:
            raise CommandError("Volume must be between 0 and 100.", True)
        assert interaction.guild is not None
        if interaction.guild.voice_client is None:
            raise CommandError("Bot is not connected to a voice channel.", True)

        assert isinstance(interaction.guild.voice_client, discord.VoiceClient)
        assert isinstance(interaction.guild.voice_client.source, discord.PCMVolumeTransformer)
        interaction.guild.voice_client.source.volume = volume / 100
        await interaction.response.send_message(f"Changed volume to {volume}%", ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def play(self, interaction: Interaction, query: str) -> None:
        """Plays from a url

        Args:
            query: The query to search for or a url to play.
        """
        await interaction.response.defer(ephemeral=True)

        assert isinstance(interaction.guild, discord.Guild)
        if not isinstance(interaction.guild.voice_client, discord.VoiceClient):
            assert isinstance(interaction.user, discord.Member)
            if interaction.user.voice is None or not isinstance(interaction.user.voice.channel, discord.VoiceChannel):
                raise CommandError("You are not connected to a voice channel.", True)
            await interaction.user.voice.channel.connect(timeout=10)
        assert isinstance(interaction.guild.voice_client, discord.VoiceClient)

        player = await YTDLSource.from_query(query, loop=self.bot.loop)
        interaction.guild.voice_client.play(player, after=lambda e: logger.error(f"Player error: {e}") if e else None)

        await interaction.followup.send(f"Now playing: {player.title}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))

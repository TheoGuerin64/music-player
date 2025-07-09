import asyncio
import logging
from asyncio import AbstractEventLoop
from collections import deque
from typing import Optional

import discord
import youtube_dl
from discord import Interaction, app_commands
from discord.ext import commands

from my_discord_bot.cogs.bot_cog import BotCog
from my_discord_bot.exceptions import CommandError

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
    "force-ipv4": True,
    "skip_download": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
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
    async def from_query(
        cls, query: str, *, loop: Optional[AbstractEventLoop] = None
    ) -> "YTDLSource":
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: cls.ytdl.extract_info(query, download=False)
        )

        assert isinstance(data, dict)
        if "entries" in data:
            data = data["entries"][0]

        return cls(discord.FFmpegPCMAudio(data["url"], options="-vn"), data=data)


class Music(BotCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.current_song: dict[int, YTDLSource] = {}
        self.queues: dict[int, deque[YTDLSource]] = {}

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def join(
        self, interaction: Interaction, channel: Optional[discord.VoiceChannel]
    ) -> None:
        """Join the voice channel.

        Args:
            channel: Voice channel to join. If not provided, joins the channel of the user who invoked the command.
        """
        if not channel:
            assert isinstance(interaction.user, discord.Member)
            if interaction.user.voice is None or not isinstance(
                interaction.user.voice.channel, discord.VoiceChannel
            ):
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

        self.queues.pop(interaction.guild.id, None)
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
        assert isinstance(
            interaction.guild.voice_client.source, discord.PCMVolumeTransformer
        )
        interaction.guild.voice_client.source.volume = volume / 100
        await interaction.response.send_message(
            f"Changed volume to {volume}%", ephemeral=True
        )

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def skip(self, interaction: Interaction) -> None:
        """Skip the current song."""
        assert interaction.guild is not None
        if interaction.guild.voice_client is None:
            raise CommandError("Bot is not connected to a voice channel.", True)

        if not self.queues.get(interaction.guild.id):
            raise CommandError("Queue is empty.", True)

        assert isinstance(interaction.guild.voice_client, discord.VoiceClient)
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped", ephemeral=True)

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
            if interaction.user.voice is None or not isinstance(
                interaction.user.voice.channel, discord.VoiceChannel
            ):
                raise CommandError("You are not connected to a voice channel.", True)
            await interaction.user.voice.channel.connect(timeout=10)

        def play_next_song(error: Optional[Exception] = None) -> None:
            if error:
                logger.error(f"Player error: {error}")

            assert isinstance(interaction.guild, discord.Guild)
            if not isinstance(interaction.guild.voice_client, discord.VoiceClient):
                logger.info("Client is not connected to voice channel.")
                if self.queues.get(interaction.guild.id):
                    self.queues.pop(interaction.guild.id)
                return

            queue = self.queues.get(interaction.guild.id)
            if queue is None:
                return
            if not queue:
                self.queues.pop(interaction.guild.id)
                return

            next_song = self.queues[interaction.guild.id].pop()
            interaction.guild.voice_client.play(next_song, after=play_next_song)
            self.current_song[interaction.guild.id] = next_song

        player = await YTDLSource.from_query(query, loop=self.bot.loop)
        if self.queues.get(interaction.guild.id) is None:
            self.queues[interaction.guild.id] = deque([player])
            play_next_song()
        elif len(self.queues[interaction.guild.id]) < 10:
            self.queues[interaction.guild.id].appendleft(player)
        else:
            raise CommandError("Queue is full.", True)

        await interaction.followup.send(
            f"Added to queue: {player.title}", ephemeral=True
        )

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def queue(self, interaction: Interaction) -> None:
        """Shows the current queue."""
        assert interaction.guild is not None
        if not self.queues.get(interaction.guild.id):
            raise CommandError("Queue is empty.", True)

        queue = self.queues[interaction.guild.id]
        embed = discord.Embed(title="Queue", color=discord.Color.blurple())

        for i, song in enumerate(reversed(queue), start=1):
            name = f"{i}. {song.title or 'Unknown Title'}"
            if len(name) > 255:
                name = name[:252] + "..."

            embed.add_field(name=name, value="", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def current(self, interaction: Interaction) -> None:
        """Shows the current song."""
        assert interaction.guild is not None
        song = self.current_song.get(interaction.guild.id)
        if song is None:
            raise CommandError("No song is currently playing.", True)

        await interaction.response.send_message(
            f"Currently playing: {song.title}", ephemeral=True
        )

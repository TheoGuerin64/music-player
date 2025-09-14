import asyncio
import logging
from asyncio import AbstractEventLoop
from collections import deque
from dataclasses import dataclass
from typing import Any, Self

import discord
import yt_dlp
from discord import AudioSource, Interaction, app_commands
from discord.ext import commands, tasks

from music_player.cogs.bot_cog import BotCog
from music_player.exceptions import CommandError

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

FFMPEG_OPTIONS: dict[str, Any] = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

QUEUE_SIZE = 9

logger = logging.getLogger(__name__)


class YTDLSource:
    _ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)

    def __init__(self, data: dict[str, Any], *, volume: float = 0.5) -> None:
        self.url = data["url"]
        self.volume = volume

        self.title = data["title"]
        self.webpage_url = data["webpage_url"]
        self.channel = data["channel"]
        self.channel_url = data["channel_url"]
        self.duration = data["duration"]
        self.thumbnail = data["thumbnails"][0]["url"]

    def audio(self) -> AudioSource:
        source = discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTIONS)
        return discord.PCMVolumeTransformer(source, volume=self.volume)

    @classmethod
    async def from_query(
        cls, query: str, *, loop: AbstractEventLoop | None = None, volume: float = 0.5
    ) -> Self:
        loop = loop or asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None, lambda: cls._ytdl.extract_info(query, download=False)
        )

        assert isinstance(data, dict)
        if "entries" in data:
            data = data["entries"][0]

        return cls(data, volume=volume)


def source_embed(source: YTDLSource) -> discord.Embed:
    minutes, seconds = divmod(source.duration, 60)
    hours, minutes = divmod(minutes, 60)
    duration = f"{minutes:d}:{seconds:02d}"
    if hours:
        duration = f"{hours:d}:{duration}"

    embed = discord.Embed(
        title=source.title,
        url=source.webpage_url,
        description=duration,
    )
    embed.set_author(name=source.channel, url=source.channel_url)
    embed.set_thumbnail(url=source.thumbnail)
    return embed


@dataclass
class GuildMusicState:
    source_queue: deque[YTDLSource]
    current_song: YTDLSource | None


class Music(BotCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.guild_states: dict[int, GuildMusicState] = {}
        self.volume_value = 0.5
        self.player_loop.start()

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def join(
        self,
        interaction: Interaction,
        channel: discord.VoiceChannel | discord.StageChannel | None = None,
    ) -> None:
        """Join the voice channel.

        Args:
            channel: Voice channel to join. If not provided, joins the channel of the user who invoked the command.
        """
        if not channel:
            user = interaction.user
            assert isinstance(user, discord.Member)

            voice = user.voice
            if voice is None or voice.channel is None:
                message = "You are not connected to a voice channel."
                raise CommandError(message, ephemeral=True)
            channel = voice.channel

        guild = interaction.guild
        assert guild is not None

        voice_client = guild.voice_client
        if voice_client is not None:
            assert isinstance(voice_client, discord.VoiceClient)

            current_channel = voice_client.channel
            if current_channel.id == channel.id:
                message = f"Already connected to {channel.name}."
                await interaction.response.send_message(message, ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        if voice_client is None:
            await channel.connect()
        else:
            await voice_client.move_to(channel)

        message = f"Joined {channel.name}"
        await interaction.followup.send(message, ephemeral=True)

    @app_commands.command()
    @app_commands.guild_only()
    async def stop(self, interaction: Interaction) -> None:
        """Stop the music and leave the voice channel."""
        guild = interaction.guild
        assert guild is not None

        voice_client = guild.voice_client
        if voice_client is None:
            message = "Bot is not connected to a voice channel."
            raise CommandError(message, ephemeral=True)
        assert isinstance(voice_client, discord.VoiceClient)

        self.guild_states.pop(guild.id, None)
        await voice_client.disconnect()

        message = "Disconnected."
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def volume(self, interaction: Interaction, volume: int) -> None:
        """Change the player volume.

        Args:
            volume: Volume to set.
        """
        if volume < 0 or volume > 100:
            message = "Volume must be between 0 and 100."
            raise CommandError(message, ephemeral=True)

        guild = interaction.guild
        assert guild is not None

        voice_client = guild.voice_client
        if voice_client is None:
            message = "Bot is not connected to a voice channel."
            raise CommandError(message, ephemeral=True)
        assert isinstance(voice_client, discord.VoiceClient)

        source = voice_client.source
        if source is None:
            message = "No audio source is playing."
            raise CommandError(message, ephemeral=True)
        assert isinstance(source, discord.PCMVolumeTransformer)

        self.volume_value = volume / 100
        source.volume = self.volume_value

        message = f"Volume set to {volume}%."
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def skip(self, interaction: Interaction) -> None:
        """Skip the current song."""
        guild = interaction.guild
        assert guild is not None

        guild_state = self.guild_states.get(guild.id)
        if guild_state is None or guild_state.current_song is None:
            message = "No song is currently playing."
            raise CommandError(message, ephemeral=True)

        voice_client = guild.voice_client
        if voice_client is None:
            message = "Bot is not connected to a voice channel."
            raise CommandError(message, ephemeral=True)
        assert isinstance(voice_client, discord.VoiceClient)

        voice_client.stop()
        guild_state.current_song = None

        if guild_state.current_song is None and not guild_state.source_queue:
            message = "Skipped. Queue is empty."
            await interaction.response.send_message(message, ephemeral=True)
            return

        next_song = guild_state.current_song or guild_state.source_queue[-1]

        embed = source_embed(next_song)
        message = "Skipped. Now playing:"
        await interaction.response.send_message(message, embed=embed, ephemeral=True)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def play(self, interaction: Interaction, query: str) -> None:
        """Plays from a url

        Args:
            query: The query to search for or a url to play.
        """
        guild = interaction.guild
        assert guild is not None

        await interaction.response.defer(ephemeral=True)

        if guild.voice_client is None:
            user = interaction.user
            assert isinstance(user, discord.Member)

            voice = user.voice
            if voice is None or voice.channel is None:
                message = "You are not connected to a voice channel."
                raise CommandError(message, ephemeral=True)

            await voice.channel.connect()

        guild_state = self.guild_states.get(guild.id)
        if guild_state is None:
            guild_state = GuildMusicState(deque(), None)

        source = await YTDLSource.from_query(
            query, loop=self.bot.loop, volume=self.volume_value
        )
        if len(guild_state.source_queue) <= QUEUE_SIZE:
            guild_state.source_queue.appendleft(source)
        else:
            message = "Queue is full."
            raise CommandError(message, ephemeral=True)

        if guild.id not in self.guild_states:
            self.guild_states[guild.id] = guild_state

        embed = source_embed(source)
        if guild_state.current_song is None and len(guild_state.source_queue) == 1:
            message = "Now playing:"
        else:
            message = "Added to queue:"
        await interaction.followup.send(message, embed=embed, ephemeral=True)

    @tasks.loop(seconds=0.5)
    async def player_loop(self) -> None:
        for guild_id, guild_state in self.guild_states.copy().items():
            guild = self.bot.get_guild(guild_id)
            if (
                guild is None
                or (guild_state.current_song is None and not guild_state.source_queue)
                or guild.voice_client is None
            ):
                self.guild_states.pop(guild_id)
                continue

            voice_client = guild.voice_client
            assert isinstance(voice_client, discord.VoiceClient)

            if voice_client.is_playing():
                continue

            guild_state.current_song = None
            if not guild_state.source_queue:
                continue

            next_song = guild_state.source_queue.pop()
            voice_client.play(next_song.audio())
            guild_state.current_song = next_song

    @player_loop.before_loop
    async def before_player_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def queue(self, interaction: Interaction) -> None:
        """Shows the current queue."""
        guild = interaction.guild
        assert guild is not None

        guild_state = self.guild_states.get(guild.id)
        if guild_state is None or (
            not guild_state.current_song and not guild_state.source_queue
        ):
            message = "Queue is empty."
            raise CommandError(message, ephemeral=True)

        full_source_queue = []
        if guild_state.current_song is not None:
            full_source_queue.append(guild_state.current_song)
        full_source_queue += list(reversed(guild_state.source_queue))

        embeds = [source_embed(source) for source in full_source_queue]
        await interaction.response.send_message(embeds=embeds, ephemeral=True)

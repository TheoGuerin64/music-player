import logging
from string import Template

import aiohttp
import discord
from discord.ext import commands, tasks

from ..db import db
from .bot_cog import BotCog

TEST_LINK = Template("https://lelscans.net/mangas/one-piece/$chapter/00.jpg")
SCAN_LINK = Template("https://lelscans.net/scan-one-piece/$chapter")

logger = logging.getLogger(__name__)


class OnePiece(BotCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.check_chapter.start()

    @tasks.loop(hours=1)
    async def check_chapter(self) -> None:
        chapter = db.get_one_piece_chapter()
        if chapter is None:
            logger.error("Chapter not found in the database.")
            return

        new_chapter = chapter + 1
        async with aiohttp.ClientSession() as session:
            async with session.get(
                TEST_LINK.substitute(chapter=new_chapter)
            ) as response:
                if response.status != 200:
                    return

        for channel_id in db.get_one_piece_channels_id():
            channel = self.bot.get_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                logger.error("Invalid channel.")
                continue

            message = f"Chapter {new_chapter} is out! {SCAN_LINK.substitute(chapter=new_chapter)}"

            role = discord.utils.get(channel.guild.roles, name="One Piece chapter")
            if role is not None:
                message = f"{role.mention} {message}"

            await channel.send(message)

        db.set_one_piece_chapter(new_chapter)

    @check_chapter.before_loop
    async def before_check_chapter(self) -> None:
        await self.bot.wait_until_ready()
        chapter = db.get_one_piece_chapter()
        if chapter is None:
            db.set_one_piece_chapter(1111)

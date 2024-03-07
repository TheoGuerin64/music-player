import logging

import discord
from discord.ext import commands

from db import db

logger = logging.getLogger(__name__)


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel_id = db.get_welcome_channel_id(member.guild.id)
        if channel_id is None:
            return

        channel = member.guild.get_channel(channel_id)
        if channel is None:
            logger.error(f"Welcome channel {channel_id} not found in guild {member.guild.id}.")
            return
        if not isinstance(channel, discord.TextChannel):
            logger.error(f"Invalid welcome channel {channel_id} in guild {member.guild.id}.")
            return

        await channel.send(f"Bienvenue {member.mention}, lis les règles et amuse toi !")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))

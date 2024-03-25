import logging

import discord
from discord.ext import commands

from db import db

logger = logging.getLogger(__name__)


class InvalidPayload(Exception):
    pass


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

    def get_role_member(self, payload: discord.RawReactionActionEvent) -> tuple[discord.Role, discord.Member]:
        if not payload.guild_id:
            raise ValueError("Guild ID not found.")

        message_id = db.get_role_message_id(payload.guild_id)
        if not message_id or payload.message_id != message_id:
            raise InvalidPayload("Message ID not found.")

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            raise ValueError("Guild not found.")

        member = guild.get_member(payload.user_id)
        if not member:
            raise ValueError("Member not found.")
        if member.bot or (self.bot.user and payload.user_id == self.bot.user.id):
            raise InvalidPayload("Bot or self user.")

        match payload.emoji.name:
            case "🏴‍☠️":
                role = discord.utils.get(guild.roles, name="One Piece chapter")
            case _:
                raise InvalidPayload("Invalid emoji.")
        if role is None:
            raise InvalidPayload("Role not found.")

        return role, member

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        try:
            role, member = self.get_role_member(payload)
        except InvalidPayload:
            return

        try:
            await member.add_roles(role)
        except discord.HTTPException as e:
            logger.error(f"Failed to add role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        try:
            role, member = self.get_role_member(payload)
        except InvalidPayload:
            return

        try:
            await member.remove_roles(role)
        except discord.HTTPException as e:
            logger.error(f"Failed to remove role: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))

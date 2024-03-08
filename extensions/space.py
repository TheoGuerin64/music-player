import random
from datetime import datetime
from enum import Enum
from string import Template
from typing import Optional

import aiohttp
import discord
from discord import Interaction, app_commands
from discord.ext import commands

from settings import NASA_API_KEY

APOD_URL = Template("https://api.nasa.gov/planetary/apod?api_key=$api_key")
ROVER_DATA_URL = Template("https://api.nasa.gov/mars-photos/api/v1/rovers/$name?api_key=$api_key")
ROVER_PHOTOS_URL = Template("https://api.nasa.gov/mars-photos/api/v1/rovers/$name/photos?$date_arg&api_key=$api_key")
EARTH_URL = Template("https://api.nasa.gov/EPIC/api/natural?api_key=$api_key")
EARTH_IMAGE_URL = Template("https://epic.gsfc.nasa.gov/archive/natural/$year/$month/$day/png/$image.png")


class Rovers(Enum):
    curiosity = "Curiosity"
    opportunity = "Opportunity"
    spirit = "Spirit"
    perseverance = "Perseverance"


async def rover_date_arg(name: str, date: Optional[str]) -> str:
    if date is None:
        url = ROVER_DATA_URL.substitute(name=name, api_key=NASA_API_KEY)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        max_sol = int(data["rover"]["max_sol"])
        return "sol=" + str(random.randint(0, max_sol))
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise app_commands.AppCommandError("Invalid date format. (format: YYYY-MM-DD)")
        return "earth_date=" + date


class Space(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()

    @app_commands.command()
    @app_commands.guild_only()
    async def apod(self, interaction: Interaction) -> None:
        """Astronomy Picture of the Day."""
        await interaction.response.defer(thinking=True)

        url = APOD_URL.substitute(api_key=NASA_API_KEY)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data: dict = await response.json()

        embed = discord.Embed(
            title=data["title"],
            description=data["explanation"]
        )
        if "copyright" in data.keys():
            embed.set_author(name=data["copyright"])
        embed.set_image(url=data["hdurl"])

        await interaction.followup.send(embed=embed)

    @app_commands.command()
    @app_commands.describe()
    @app_commands.guild_only()
    async def rover(self, interaction: Interaction, name: Optional[Rovers], date: Optional[str]) -> None:
        """Random picture of Mars rover.

        Args:
            name: Name of the rover to get a picture of.
            date: Date when the photo was taken. (format: YYYY-MM-DD)
        """
        await interaction.response.defer(thinking=True)

        rover_name = name.value if name else random.choice(list(Rovers)).value
        date_arg = await rover_date_arg(rover_name, date)

        url = ROVER_PHOTOS_URL.substitute(name=rover_name, date_arg=date_arg, api_key=NASA_API_KEY)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        if not data["photos"]:
            raise app_commands.AppCommandError("No pictures found, try again.")
        photo = random.choice(data["photos"])

        embed = discord.Embed(timestamp=datetime.strptime(photo["earth_date"], "%Y-%m-%d"))
        embed.set_author(name=photo["rover"]["name"])
        embed.set_image(url=photo["img_src"])
        await interaction.followup.send(embed=embed)

    @app_commands.command()
    @app_commands.guild_only()
    async def earth(self, interaction: Interaction) -> None:
        """Random picture of Earth."""
        await interaction.response.defer(thinking=True)

        url = EARTH_URL.substitute(api_key=NASA_API_KEY)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        photo = random.choice(data)
        date = datetime.strptime(photo["date"], "%Y-%m-%d %H:%M:%S")
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)

        embed = discord.Embed(timestamp=date)
        embed.set_image(url=EARTH_IMAGE_URL.substitute(year=date.year, month=month, day=day, image=photo["image"]))
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Space(bot))

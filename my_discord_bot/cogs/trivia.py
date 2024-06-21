from random import shuffle
from string import Template
from typing import Optional

import aiohttp
import discord
from discord import Interaction, app_commands
from discord.app_commands import Choice

from .bot_cog import BotCog

URL_TEMPLATE = Template(
    "https://the-trivia-api.com/api/questions?limit=1&difficulty=$difficulty&categories=$category"
)


class Retry(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Retry", style=discord.ButtonStyle.blurple)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, TriviaView)
        await self.view.retry(interaction)


class Answer(discord.ui.Button):
    def __init__(self):
        super().__init__()
        self.is_correct = False

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, TriviaView)
        await self.view.click_button(interaction, self)


class TriviaView(discord.ui.View):
    def __init__(self, difficulty: str, category: str) -> None:
        super().__init__(timeout=None)
        self.difficulty = difficulty
        self.category = category

        for _ in range(4):
            self.add_item(Answer())
        self.add_item(Retry())

    async def click_button(self, interaction: Interaction, button: Answer) -> None:
        for child in self.children:
            if not isinstance(child, Answer):
                continue
            if child.is_correct or child is button:
                child.style = (
                    discord.ButtonStyle.green if child.is_correct else discord.ButtonStyle.red
                )
            child.disabled = True
        await interaction.response.edit_message(view=self)

    async def request_trivia(self) -> dict:
        url = URL_TEMPLATE.substitute(difficulty=self.difficulty, category=self.category)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return (await response.json())[0]

    async def generate_questions(self) -> discord.Embed:
        data = await self.request_trivia()

        embed = discord.Embed(title=data["question"])
        embed.set_author(name=data["category"])
        embed.set_footer(text=data["difficulty"].capitalize())

        answers = [data["correctAnswer"]] + data["incorrectAnswers"]
        shuffle(answers)
        for button, answer in zip(self.children, answers):
            if isinstance(button, Answer):
                button.label = answer
                button.is_correct = answer == data["correctAnswer"]
                button.style = discord.ButtonStyle.grey
                button.disabled = False

        return embed

    async def start(self, interaction: Interaction) -> None:
        embed = await self.generate_questions()
        await interaction.response.send_message(embed=embed, view=self, ephemeral=True)

    async def retry(self, interaction: Interaction) -> None:
        embed = await self.generate_questions()
        await interaction.response.edit_message(embed=embed, view=self)


class Trivia(BotCog):
    @app_commands.command()
    @app_commands.describe()
    @app_commands.choices(
        difficulty=[
            Choice(name="Easy", value="easy"),
            Choice(name="Medium", value="medium"),
            Choice(name="Hard", value="hard"),
        ],
        category=[
            Choice(name="Arts and Literature", value="arts_and_literature"),
            Choice(name="Film and TV", value="film_and_tv"),
            Choice(name="Food and Drink", value="food_and_drink"),
            Choice(name="General Knowledge", value="general_knowledge"),
            Choice(name="Geography", value="geography"),
            Choice(name="History", value="history"),
            Choice(name="Music", value="music"),
            Choice(name="Science", value="science"),
            Choice(name="Society and Culture", value="society_and_culture"),
            Choice(name="Sport and Leisure", value="sport_and_leisure"),
        ],
    )
    async def trivia(
        self,
        interaction: Interaction,
        difficulty: Optional[Choice[str]],
        category: Optional[Choice[str]],
    ) -> None:
        """Start a trivia.

        Args:
            difficulty: The difficulty of the trivia.
            category: The category of the trivia.
        """
        await TriviaView(
            difficulty.value if difficulty is not None else "",
            category.value if category is not None else "",
        ).start(interaction)

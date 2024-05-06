import discord
from discord.ext import commands
from discord import app_commands

from datetime import datetime
import os
import asyncio
import glob

import logging

import libraries.APIs.config as configLib 

bot = None

if __name__ == "__main__":
    config = configLib.getConfig()
    
    directories = ["temp", "logs"]
    for dir in directories:
        if not os.path.exists(dir):
            os.mkdir(dir)
        if config["DEVELOPMENT"]:
            for file in os.listdir(dir):
                os.remove(f"{dir}/{file}")
    
    logging.basicConfig(
        level=logging.INFO,
        filename=f"logs/{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.log",
        filemode="w",
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    )

    logging.warning("warning")
    logging.error("error")
    logging.critical("critical")


    class Bot(commands.AutoShardedBot):
        def __init__(self, *args, **kwargs):
            self.config = config
            
            super().__init__(
                shards=self.config["SHARDS"],
                command_prefix=(self.get_prefix),
                strip_after_prefix=True,
                case_insensitive=True,
                owner_ids=self.config["OWNER_IDS"],
                intents=discord.Intents.all(),
                allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=False),
            *args, **kwargs)

            self.start_time = datetime.now()

        async def on_ready(self) -> None:
            print(f"Succesfully logged in as {self.user}")
        
        async def setup_hook(self) -> None:            
            if self.config["SYNC_TREE"]:
                print(f"Syncing command tree...")
                if self.config["DEVELOPMENT"]:
                    guild = discord.Object(id=self.config["DEVELOPMENT_GUILD"])
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync()
                else:
                    await self.tree.sync()
                print(f"Command tree synced!")
            else:
                print(f"{self.user} is set to not sync tree, continuing")
        
        
        async def get_prefix(self, message):
            return commands.when_mentioned_or(*config["PREFIXES"])(self, message)
        

    bot = Bot()

    @bot.tree.command(
        name="testcommand",
        description="My first application Command",
        guild=discord.Object(id=bot.config["DEVELOPMENT_GUILD"])
    )
    async def first_command(interaction):
        await interaction.response.send_message("Hello!")
    
    
    async def main():
        async with bot:
            for filename in glob.iglob("./cogs/**", recursive=True):
                if filename.endswith(".py"):
                    # goes from "./cogs/economy.py" to "cogs.economy.py"
                    filename = filename[2:].replace("/", ".")[:-3]
                    # removes the ".py" from the end of the filename, to make it into cogs.economy
                    await bot.load_extension(filename)

            await bot.start(bot.config["API_KEYS"]["DISCORD"])

    asyncio.run(main())



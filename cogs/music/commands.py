import discord
from discord.ext import commands
from discord import app_commands

import asyncio

import libraries.helpers as helpers
import libraries.music_handler as music_handler

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = bot.cogs["MusicPlayer"]

    @commands.command(
        name="play",
        description="plays a song")
    async def play_command(self, ctx, *, song):
        try:
            voice_channel = ctx.author.voice.channel
        
        except AttributeError as e:
            await ctx.send("couldn't find the voice channel you're in, perhaps you're not in a voice channel?")
            return

        except Exception as e:
            await ctx.send(f"an exception was thrown:\n{e}")
            return

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild) # This allows for more functionality with voice channels
        guild_id = ctx.guild.id
        
        await music_handler.ensure_valid_data(self.player, guild_id)
        self.player.data[guild_id]["queue"].append(
            {"url": song, "data": None}
        )

        await ctx.message.add_reaction("✅")
        
        if voice_client == None:
            await voice_channel.connect(self_deaf=True)
            await self.player.play_song(ctx)
        
        else:
            if voice_client.channel != voice_channel:
                await ctx.send("sorry, i'm already busy playing another banger in this guild")
                return
            
            queue = self.player.data[guild_id]["queue"]
            index = len(queue) - 1
            
            if not self.player.data[guild_id]["playing"]:
                await self.player.play_song(ctx)
            else:
                await self.player.cache_song(guild_id, index)
                data = await music_handler.get_meta_data(queue[index]["data"])
                
                embed = helpers.create_embed(ctx)
                embed.title = "Added song to queue"
                embed.description = data["title"]

                embed = await music_handler.add_embed_fields(embed, data)
                
                await ctx.send(embed = embed)

    
    @commands.command(
        name="nowplaying", aliases=["now-playing", "np"],
        description="In case you're wondering what song i'm playing")
    async def nowplaying_command(self, ctx):
        guild_id = ctx.guild.id
        if not guild_id in self.player.data or self.player.data[guild_id]["playing"] == False:
            await ctx.send("sorry, i'm currently not playing any songs within this server")
            return
        
        meta_data = self.player.data[guild_id]["meta_data"]
        
        embed = helpers.create_embed(ctx)
        embed.title = "Currently Playing"
        embed.description = meta_data["title"]
        
        progress = self.player.data[guild_id]["progress"] / 1000
        progress_bar = helpers.getProgressBar(progress, meta_data["duration"], 23)
        embed.add_field(
            name="Progress",
            value=f"{round((progress / meta_data['duration']) * 100)}% - {progress_bar}",
            inline=False
        )

        embed = await music_handler.add_embed_fields(embed, meta_data)
        
        await ctx.send(embed = embed)

    @commands.command(name="move", aliases=["psps"])
    async def move_command(self, ctx):
        voice_channel = ctx.author.voice.channel
        
        if voice_channel is not None:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice.pause()
            await ctx.send(f"oke, moving to {voice_channel.name}")
            await voice.move_to(voice_channel)
            await asyncio.sleep(2)
            voice.resume()
        else:
            await ctx.send("it doesn't seem like you're in a voice channel")
    
    @commands.command(
        name="skip",
        description="pikmin!")
    async def skip_command(self, ctx):
        # this stops the song, making the next song automatically start
        discord.utils.get(self.bot.voice_clients, guild=ctx.guild).stop()
    
    @commands.hybrid_command(
        name="stop", aliases=["leave", "disconnect"],
        description="Pikmin :(")
    async def stop_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            await voice.disconnect()
            await ctx.send("okay, i'll stop")
        else:
            await ctx.send("sorry, i don't seem to be in any voice channels at the moment")
        del self.player.data[ctx.guild.id]


async def setup(bot):
    await bot.add_cog(MusicCommands(bot))

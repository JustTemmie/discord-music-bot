import discord
from discord.ext import commands

import asyncio
import aiohttp
import yt_dlp

import libraries.helpers as helpers
import libraries.music_handler as music_handler

ytdlp_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
    'retries': "infinite"
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdlp = yt_dlp.YoutubeDL(ytdlp_format_options)

class TrackedFFmpegPCMAudio(discord.FFmpegPCMAudio):
    def __init__(self, player, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = player
        self.guild_id = guild_id

    def read(self, *args, **kwargs):
        ret = super().read()
        if ret:
            self.player.data[self.guild_id]["progress"] += 20
        return ret
    
class YtDlpSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')


    @classmethod
    async def next_song(cls, player, guild_id):
        song = player.data[guild_id]["queue"].pop(0)
        
        if song["data"] == None:
            data = await player.download_song(song["url"])
        else:
            data = song["data"]
        
        filename = data['url']
        
        player.data[guild_id]["meta_data"] = await music_handler.get_meta_data(data)
        player.data[guild_id]["progress"] = 0        
        
        return cls(TrackedFFmpegPCMAudio(player, guild_id, filename, **ffmpeg_options), data=data)

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
    
    async def download_song(self, url):
        data = await asyncio.get_event_loop().run_in_executor(None, lambda: ytdlp.extract_info(url, download=False))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        
        return data
    
    async def cache_song(self, guild_id, index = 0):
        if len(self.data[guild_id]["queue"]) == 0:
            return
        
        self.data[guild_id]["next_up"] = "pending"
        
        url = self.data[guild_id]["queue"][index]["url"]
        data = await self.download_song(url)
        
        self.data[guild_id]["queue"][index]["data"] = data
        # print(f"finished downloading cache for {url}")
    
    async def play_song(self, ctx):
        try:
            if len(self.data[ctx.guild.id]["queue"]) == 0:
                self.data["playing"] = False 
                await music_handler.send_queue_finished_embed(ctx)
                return
            
            self.data[ctx.guild.id]["playing"] = True
            
            
            player = await YtDlpSource.next_song(self, ctx.guild.id)
            
            ctx.voice_client.play(
                player,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_song(ctx), self.bot.loop
                )
            )
            
            await music_handler.send_now_playing_embed(self, ctx)
        
        except Exception as err:
            error = f"whoopsie, it looks like i encountered an error whilst trying to play your song\n{type(err)}:\n```{err}```"
            print(error)
            await ctx.send(error)
    

async def setup(bot):
    await bot.add_cog(MusicPlayer(bot))

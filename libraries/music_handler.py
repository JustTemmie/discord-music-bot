import aiohttp

import libraries.helpers as helpers

async def get_like_dislike_ratio(video_id):
    if video_id == "unknown":
        return {}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}") as r:
            if r.status == 200:
                data = await r.json()
                meta_data = {
                    "likes": data["likes"],
                    "dislikes": data["dislikes"],
                    "views": data["viewCount"],
                }
            else:
                meta_data = {
                    "likes": "unknown",
                    "dislikes": "unknown",
                    "views": "unknown",
                }

    return meta_data
    
async def ensure_valid_data(player, guild_id):
    # make sure there's actually usable data in the data dictionary
    if guild_id not in player.data:
        player.data[guild_id] = {}
        player.data[guild_id]["playing"] = False
        player.data[guild_id]["meta_data"] = {}
        player.data[guild_id]["settings"] = {}
        player.data[guild_id]["queue"] = []
        player.data[guild_id]["progress"] = 0

async def send_now_playing_embed(player, ctx):
    meta_data = player.data[ctx.guild.id]["meta_data"]
    
    embed = helpers.create_embed(ctx)
    embed.title = meta_data["title"]
    embed.description = "Now Playing"

    embed = await add_embed_fields(embed, meta_data)
    
    await ctx.send(embed=embed)

async def add_embed_fields(embed, meta_data):
        existing_field_count = len(embed.fields)
        
        # LIVE STATUS
        if meta_data["live_status"] == "is_live":
            embed.add_field(
                name = "Type",
                value = "Livestream")
        
        # DURATION
        if meta_data["readable_duration"] != "unknown":
            embed.add_field(
                name = "Duration",
                value = meta_data["readable_duration"])
        
        # UPLOADER
        if meta_data["uploader"] != "unknown":
            embed.add_field(
                name="Uploader",
                value=f"[{meta_data['uploader']}]({meta_data['uploader_url']})")
        
        # LIKE DISLIKE RATIO
        if meta_data["dislikes"] != "unknown":
            embed.add_field(
                name="Likes / Dislikes",
                value=f"{meta_data['likes']} / {meta_data['dislikes']}",
            )
            
        # VIEW COUNT
        if meta_data["views"] != "unknown":
            embed.add_field(
                name="views",
                value=meta_data["views"])
            
        # THUMBNAIL
        if meta_data["thumbnail"] != "unknown":
            embed.set_thumbnail(url = meta_data["thumbnail"])
        
        new_field_count = len(embed.fields)
        
        for i in range(new_field_count - 2, max(0, existing_field_count - 1), -2):
            embed.insert_field_at(
                i,
                name="\t",
                value="\t",
                inline=False
            )
        
        
        return embed

async def send_queue_finished_embed(ctx):
    embed = helpers.create_embed(ctx)
    embed.title = "Queue Finished"
    await ctx.send(embed = embed)

async def get_meta_data(data, fetch_like_dislike_ratio = True):
    video_id = data["id"]
    if video_id == None: video_id = "unknown"
    if fetch_like_dislike_ratio:
        meta_data = await get_like_dislike_ratio(video_id)
    else:
        meta_data = {}
    
    data_points = ["title", "duration", "live_status", "upload_date", "uploader", "uploader_url", "thumbnail"]

    for entry in data_points:
        if entry in data:
            meta_data[entry] = data[entry]
        else:
            meta_data[entry] = "unknown"
    
    if "duration" in data:
        meta_data["readable_duration"] = helpers.format_time(data["duration"])
    else:
        meta_data["readable_duration"] = "unknown"
    
    return meta_data
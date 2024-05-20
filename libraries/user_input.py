import asyncio

async def get_input(bot, ctx, time=20, bonus=""):
    try:
        response = await bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=time)
        return response
    except asyncio.TimeoutError:
        await ctx.send(f"**Timed out** You took too long to answer the question{bonus}")
        return None

async def get_consent(bot, ctx, time, bonus=""):
    response = await get_input(bot, ctx, time, bonus)
    if response == None:
        return False
    
    if response.content.lower()[0] == "y":
        return True
    else:
        return False

import discord
from discord.ext import commands
import io
import aiohttp
import json
import asyncio
from config import BOT_TOKEN, ADMIN_ID
from database import *

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user}')
    for guild in bot.guilds:
        for ch in guild.channels:
            if isinstance(ch, (discord.TextChannel, discord.ForumChannel)):
                if not get_channel_permission(str(ch.id)):
                    set_channel_permission(str(ch.id), ch.name, {"can_send":1, "can_attach":1, "can_delete":0})
                    print(f"📌 Registered #{ch.name}")

@bot.command(hidden=True)
@commands.is_owner()
async def api_send(ctx, channel_id: str, content: str = "", embed_json: str = "{}", file_url: str = ""):
    channel = bot.get_channel(int(channel_id))
    if not channel:
        await ctx.send("❌ Channel not found")
        return
    
    perm = get_channel_permission(channel_id)
    if not perm or not perm['can_send']:
        await ctx.send("❌ No send permission")
        return
    
    file_obj = None
    if file_url and perm['can_attach']:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        fname = file_url.split('/')[-1].split('?')[0] or 'file.bin'
                        file_obj = discord.File(io.BytesIO(data), filename=fname[:50])
        except Exception as e:
            print(f"File download error: {e}")
    
    embed = None
    if embed_json and embed_json != "{}":
        try:
            e_data = json.loads(embed_json)
            embed = discord.Embed(
                title=e_data.get('title'),
                description=e_data.get('description'),
                color=int(e_data.get('color', '#5865F2').replace('#',''), 16)
            )
            for field in e_data.get('fields', []):
                embed.add_field(name=field.get('name'), value=field.get('value'), inline=field.get('inline', False))
            if e_data.get('image'):
                embed.set_image(url=e_data.get('image'))
            if e_data.get('footer'):
                embed.set_footer(text=e_data.get('footer'))
        except Exception as e:
            print(f"Embed error: {e}")
    
    try:
        if file_obj and embed:
            msg = await channel.send(content=content or None, embed=embed, file=file_obj)
        elif file_obj:
            msg = await channel.send(content=content or None, file=file_obj)
        elif embed:
            msg = await channel.send(content=content or None, embed=embed)
        else:
            msg = await channel.send(content or ".")
        
        log_sent_message(str(msg.id), str(channel.id), content, embed_json, file_url)
        await ctx.send(f"✅ Sent: {msg.jump_url}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(hidden=True)
@commands.is_owner()
async def api_delete(ctx, channel_id: str, message_id: str):
    channel = bot.get_channel(int(channel_id))
    if not channel:
        await ctx.send("❌ Channel not found")
        return
    perm = get_channel_permission(channel_id)
    if not perm or not perm['can_delete']:
        await ctx.send("❌ No delete permission")
        return
    try:
        msg = await channel.fetch_message(int(message_id))
        await msg.delete()
        delete_sent_message_log(message_id)
        await ctx.send(f"✅ Deleted")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(hidden=True)
@commands.is_owner()
async def api_pin(ctx, channel_id: str, message_id: str):
    channel = bot.get_channel(int(channel_id))
    if not channel:
        await ctx.send("❌ Channel not found")
        return
    try:
        msg = await channel.fetch_message(int(message_id))
        await msg.pin()
        await ctx.send(f"✅ Pinned")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def sync_channels(ctx):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("❌ No permission")
    for ch in ctx.guild.channels:
        if isinstance(ch, (discord.TextChannel, discord.ForumChannel)):
            set_channel_permission(str(ch.id), ch.name, {"can_send":1, "can_attach":1, "can_delete":0})
    await ctx.send("✅ All channels synced!")

if __name__ == "__main__":
    init_db()
    bot.run(BOT_TOKEN)

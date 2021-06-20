import discord
import os
from discord.ext import commands, tasks
from keep_alive import keep_alive
from dotenv import load_dotenv
import time
import datetime
import asyncio
import math
import aiosqlite
import discord
from discord.ext import commands
import youtube_dl





bot = commands.Bot(command_prefix=commands.when_mentioned_or('r!'), case_insensitive=True)
bot.multiplier = 4

@bot.event
async def on_ready():
  await bot.change_presence(activity=discord.Game (name="r!help"))
  print("The bot is ready.")

#DONT TOUCH EXPDATA.DB EVERRRRRRRRRRR

#utils / bot.events end, please put all bot.events up here to make it more orginized
#or however u spell it
@bot.command()
async def ping(ctx):
    start = time.perf_counter()
    message = await ctx.send("Ping...")
    end = time.perf_counter()
    duration = (end - start) * 1000
    await message.edit(content='Pong! {:.2f}ms'.format(duration))

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason) 
    await ctx.send(f"I have kicked {member.mention} for {reason}.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason=None):
    await member.ban(reason=reason) 
    await ctx.send(f"I have banned {member.mention} for {reason}.")

@bot.command()
async def unban(ctx, *, member):
  banned_users = await ctx.guild.bans()
  member_name, member_discriminator = member.split('#')

  for ban_entry in banned_users:
    user = ban_entry.user

    if (user.name, user.member_discriminator) == (member_name, member_discriminator):
      await ctx.guild.unban(user)
      await ctx.send(f'Unbanned {user.mention}')
      return

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int):
        await ctx.channel.purge(limit=limit)
        await ctx.send('Messages cleared by {}'.format(ctx.author.mention))
        await ctx.message.delete()
#moosic
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}   

def endSong(guild, path):
    os.remove(path)                                   

@bot.command()
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send('you are not connected to a voice channel')
        return

    else:
        channel = ctx.message.author.voice.channel

    voice_client = await channel.connect()


    guild = ctx.message.guild

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        file = ydl.extract_info(url, download=True)
        path = str(file['title']) + "-" + str(file['id'] + ".mp3")

    voice_client.play(discord.FFmpegPCMAudio(path), after=lambda x: endSong(guild, path))
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source, 1)

    await ctx.send(f'**Music: **{url}')


@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.command()
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.command()
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command()
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")
#reminder shit

#bot commands end (do not put anything after this except the code below, if you make a new command, do it above this. i am trying to make this look neat without cogs lol.)
#leveling
async def initialize():
 await bot.wait_until_ready()
 bot.db = await aiosqlite.connect("expData.db")
 await bot.db.execute("CREATE TABLE IF NOT EXISTS guildData (guild_id int, user_id int, exp int, PRIMARY KEY (guild_id, user_id))")

@bot.event
async def on_message(message):
    if not message.author.bot:
        cursor = await bot.db.execute("INSERT OR IGNORE INTO guildData (guild_id, user_id, exp) VALUES (?,?,?)", (message.guild.id, message.author.id, 1)) 

        if cursor.rowcount == 0:
            await bot.db.execute("UPDATE guildData SET exp = exp + 1 WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
            cur = await bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
            data = await cur.fetchone()
            exp = data[0]
            lvl = math.sqrt(exp) / bot.multiplier
        
            if lvl.is_integer():
                await message.channel.send(f"{message.author.mention} you have leveled up. You are now level {int(lvl)}.")

        await bot.db.commit()

    await bot.process_commands(message)

@bot.command(aliases=['lvl', 'stats', 'level'])
async def rank(ctx, member: discord.Member=None):
    if member is None: member = ctx.author

    # get user exp
    async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id)) as cursor:
        data = await cursor.fetchone()
        exp = data[0]

        # calculate rank
    async with bot.db.execute("SELECT exp FROM guildData WHERE guild_id = ?", (ctx.guild.id,)) as cursor:
        rank = 1
        async for value in cursor:
            if exp < value[0]:
                rank += 1

    lvl = int(math.sqrt(exp)//bot.multiplier)

    current_lvl_exp = (bot.multiplier*(lvl))**2
    next_lvl_exp = (bot.multiplier*((lvl+1)))**2

    lvl_percentage = ((exp-current_lvl_exp) / (next_lvl_exp-current_lvl_exp)) * 100

    embed = discord.Embed(title=f"Stats for {member.name}", colour=discord.Colour.purple())
    embed.add_field(name="Level", value=str(lvl))
    embed.add_field(name="Exp", value=f"{exp}/{next_lvl_exp}")
    embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}")
    embed.add_field(name="Level Progress", value=f"{round(lvl_percentage, 2)}%")

    await ctx.send(embed=embed)

bot.loop.create_task(initialize())
keep_alive()
token = os.environ.get("TOKEN")
bot.run(token)
asyncio.run (bot.db.close())

import asyncio
import json
import discord
import requests
import feedparser
import config
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from datetime import datetime

TOKEN = config.TOKEN
PREFIX = config.PREFIX
client = commands.Bot(command_prefix=config.PREFIX, case_insensitive=True)
client.remove_command("help")

@client.event
async def on_ready():
    print('ready')
    await client.change_presence(activity=discord.Activity(name="for new episodes and chapters", type=discord.ActivityType.watching))
    check_manga.start()
    check_anime.start()

@tasks.loop(seconds=180)
async def check_manga():
    with open("data.json") as f:
        data = json.load(f)
    rss = feedparser.parse("https://mangadex.org/rss/kTE6Af43prFPtdnBaMbvhKD5ySg2GeqC").entries
    rss_id = {e.mangalink.split("/")[-1] for e in rss}
    id_list = rss_id & set(data["manga"])
    for id in id_list:
        url = 'https://mangadex.org/title/' + id
        headers = {'User-Agent':'Mozilla/5.0'}
        r = requests.get(url, headers)
        soup = BeautifulSoup(r.content, "html.parser")
        newest = soup.find("div", {"data-lang":"1"})
        if newest and newest['data-chapter'] != data["manga"][id]["ch"]:
            data["manga"][id]["ch"] = newest["data-chapter"]
            data["manga"][id]["chtitle"] = newest['data-title']
            data["manga"][id]["url"] = newest['data-id']
            data["manga"][id]["title"] = soup.find("span", {"class":"mx-1"}).text
            data["manga"][id]["image"] = soup.find("img", {"class":"rounded"})['src']
            data["new_manga"].append(id)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("checked manga at", datetime.now().strftime("%H:%M:%S"))
    if data["new_manga"]:
        await notify_manga()

async def notify_manga():
    with open("data.json") as f:
        data = json.load(f)
    for guild in data["guilds"]:
        for manga in data["guilds"][guild]["manga_list"]:
            if manga in data["new_manga"]:
                title = data["manga"][manga]["title"]
                ch = data["manga"][manga]["ch"]
                chtitle = data["manga"][manga]["chtitle"]
                url = data["manga"][manga]["url"]
                image = data["manga"][manga]["image"]
                embed=discord.Embed(title=f"Chapter {ch}: {chtitle}", url=f"https://mangadex.org/chapter/{url}", color=0xf7931e, timestamp=datetime.utcnow())
                embed.set_author(name=f"{title} 📚", url=f"https://mangadex.org/title/{manga}", icon_url="https://mangadex.org/images/misc/default_brand.png")
                embed.set_image(url=f"{image}")
                embed.set_footer(text="🤖 動漫-BOT")
                await client.get_channel(int(data["guilds"][guild]["channels"][0])).send(embed=embed)

    print("notified manga")
    await clear_manga()

async def clear_manga():
    with open("data.json") as f:
        data = json.load(f)
    data["new_manga"] = []
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("cleared manga")

@tasks.loop(seconds=180)
async def check_anime():
    with open("data.json") as f:
        data = json.load(f)
    for id in data["anime"]:
        url = 'https://4anime.to/anime/' + id
        headers = {'User-Agent':'Mozilla/5.0'}
        r = requests.get(url, headers)
        soup = BeautifulSoup(r.content, "html.parser")
        ep = soup.select("a[href*=episode]")[-1].getText()
        if ep != data["anime"][id]["ep"]:
            data["anime"][id]["title"] = soup.find("p", {"class":"single-anime-desktop"}).getText()
            data["anime"][id]["ep"] = ep
            data["anime"][id]["image"] = soup.find("div", {"class":"cover"}).find('img').attrs['src']
            data["new_anime"].append(id)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("checked anime at", datetime.now().strftime("%H:%M:%S"))
    if data["new_anime"]:
        await notify_anime()

async def notify_anime():
    with open("data.json") as f:
        data = json.load(f)
    for guild in data["guilds"]:
        for anime in data["guilds"][guild]["anime_list"]:
            if anime in data["new_anime"]:
                title = data["anime"][anime]["title"]
                ep = data["anime"][anime]["ep"]
                image = data["anime"][anime]["image"]
                embed=discord.Embed(title=f"Episode {ep}", url=f"https://4anime.to/{anime}-episode-{ep}", color=0xdf1e34, timestamp=datetime.utcnow())
                embed.set_author(name=f"{title} 📺", url=f"https://4anime.to/{anime}", icon_url="https://4anime.to/static/logo.png")
                embed.set_image(url=f"https://4anime.to{image}")
                embed.set_footer(text="🤖 動漫-BOT")
                await client.get_channel(int(data["guilds"][guild]["channels"][0])).send(embed=embed)

    print("notified anime")
    await clear_anime()

async def clear_anime():
    with open("data.json") as f:
        data = json.load(f)
    data["new_anime"] = []
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("cleared anime")

@client.command()
async def add(ctx, type=None, id=None):
    if type and id:
        with open("data.json") as f:
            data = json.load(f)
        if not id in data["guilds"][str(ctx.message.guild.id)][f"{type}_list"]:
            await db(ctx, data, type, id)
        else:
            await ctx.message.add_reaction('\U0001F610')
            d = f"Already added {id}."
            embed = discord.Embed(description=d, color=discord.Colour.light_gray())
            await ctx.send(embed=embed)
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)
    else:
        d = f"`{PREFIX}add [manga/anime] [id]`"
        embed = discord.Embed(title="Syntax:", description=d, color=discord.Colour.light_gray())
        await ctx.send(embed=embed)

async def db(ctx, data, type, id):
    if type == "manga":
        if not 'does not exist' in requests.get(f"http://mangadex.org/title/{id}").text:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].append(id)
            if not id in data[type]:
                await ctx.message.add_reaction('\U00002705')
                data["manga"][id] = {"title":"", "ch":"", "chtitle":"", "url":"", "image":""}
                d = f"Added {id}."
                embed = discord.Embed(description=d, color=discord.Colour.green())
                await ctx.send(embed=embed)
        else:
            d = "Invalid MangaDex ID."
            embed = discord.Embed(description=d, color=discord.Colour.light_gray())
            await ctx.send(embed=embed)
    if type == "anime":
        if requests.get(f"http://4anime.to/title/{id}").status_code < 400:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].append(id)
            if not id in data[type]:
                await ctx.message.add_reaction('\U00002705')
                data["anime"][id] = {"ep":"", "title":"", "image":""}
                d = f"Successfully added {id}."
                embed = discord.Embed(description=d, color=discord.Colour.green())
                await ctx.send(embed=embed)
        else:
            d = "Invalid 4anime ID."
            embed = discord.Embed(description=d, color=discord.Colour.light_gray())
            await ctx.send(embed=embed)

@client.command()
async def remove(ctx, type=None, id=None):
    if type and id:
        with open("data.json") as f:
            data = json.load(f)
        try:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].remove(str(id))
        except ValueError:
            d = f"{id} is not in {type} list."
            embed = discord.Embed(description=d, color=discord.Colour.light_gray())
            await ctx.send(embed=embed)
            return
        with open("data.json", "w") as f:
            d = f"Removed {id}"
            embed = discord.Embed(description=d, color=discord.Colour.red())
            await ctx.send(embed=embed)
            json.dump(data, f, indent=4)
    else:
        d = f"`{PREFIX}remove [manga/anime] [id]`"
        embed = discord.Embed(title="Syntax:", description=d, color=discord.Colour.light_gray())
        await ctx.send(embed=embed)

@client.command()
async def list(ctx, type=None):
    with open("data.json") as f:
        data = json.load(f)
    if type:
        arr = sorted(data["guilds"][str(ctx.message.guild.id)][f"{type}_list"])
        d = "\n".join(arr)
        embed = discord.Embed(description=d, color=discord.Colour.green())
        await ctx.send(embed=embed)
    else:
        d = f"`{PREFIX}list [manga/anime]`"
        embed = discord.Embed(title="Syntax:", description=d, color=discord.Colour.light_gray())
        await ctx.send(embed=embed)

@client.command()
async def start(ctx):
    with open("data.json") as f:
        data = json.load(f)
    if str(ctx.message.guild.id) in data["guilds"]:
        d = f"__{ctx.message.guild.name}__ already added."
        embed = discord.Embed(description=d, color=discord.Colour.blue())
    else:
        data["guilds"][str(ctx.message.guild.id)] = {"channels":[str(ctx.message.channel.id)], "manga_list":[], "anime_list":[]}
        d = f"__{ctx.message.guild.name}__ added to 動漫-BOT"
        embed = discord.Embed(description=d, color=discord.Colour.blue())
    await ctx.send(embed=embed)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@client.command()
async def move(ctx):
    with open("data.json") as f:
        data = json.load(f)
    data["guilds"][str(ctx.message.guild.id)]["channels"].pop(0)
    data["guilds"][str(ctx.message.guild.id)]["channels"].append(str(ctx.message.channel.id))
    d = f"Notifications will be sent in this channel."
    embed = discord.Embed(description=d, color=discord.Colour.blue())
    await ctx.send(embed=embed)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@client.command()
async def help(ctx):
    embed=discord.Embed(description=f"To get started, type `{PREFIX}start`.\nType each command for its syntax.", color=discord.Colour.blue())
    embed.add_field(name=f"{PREFIX}add", value="Add series to track", inline=False)
    embed.add_field(name=f"{PREFIX}remove ", value="Remove series to track", inline=False)
    embed.add_field(name=f"{PREFIX}list", value="List tracked series", inline=False)
    embed.add_field(name=f"{PREFIX}move", value="Move notification channel", inline=False)
    await ctx.send(embed=embed)

client.run(TOKEN)

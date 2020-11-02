import asyncio
import json
import discord
import requests
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

client = commands.Bot(command_prefix = '^')

@client.event
async def on_ready():
    print('ready')
    await client.change_presence(activity = discord.Activity(name = "for new chapters", type = discord.ActivityType.watching))
    check_manga.start()
    check_anime.start()

@tasks.loop(seconds=600)
async def check_manga():
    with open("data.json") as f:
        data = json.load(f)
    for id in data["manga"]:
        url = 'https://mangadex.org/title/' + id
        headers = {'User-Agent':'Mozilla/5.0'}
        r = requests.get(url, headers)
        soup = BeautifulSoup(r.content, "html.parser")
        newest = soup.find("div", {"data-lang":"1"})
        ch = newest['data-chapter']
        if ch != data["manga"][id]["ch"]:
            data["manga"][id]["ch"] = ch
            data["manga"][id]["title"] = newest['data-title']
            data["manga"][id]["url"] = newest['data-id']
            data["manga"][id]["title"] = soup.find("span", {"class":"mx-1"}).text
            data["manga"][id]["image"] = soup.find("img", {"class":"rounded"})['src']
            data["new_manga"].append(id)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

    print("checked manga")
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
                embed=discord.Embed(title=f"Chapter {ch}: {chtitle}", url=f"https://mangadex.org/chapter/{url}", color=0xfaa61a)
                embed.set_author(name=f"{title}", icon_url="https://cdn.discordapp.com/embed/avatars/3.png")
                embed.set_image(url=f"{image}")
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

@tasks.loop(seconds=600)
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

    print("checked anime")
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
                embed=discord.Embed(title=f"Episode {ep}", url=f"https://4anime.to/{anime}-episode-{ep}", color=0xfaa61a)
                embed.set_author(name=f"{title}", icon_url="https://cdn.discordapp.com/embed/avatars/3.png")
                embed.set_image(url=f"https://4anime.to{image}")
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
async def add(ctx, type = None, id = None):
    if type and id:
        with open("data.json") as f:
            data = json.load(f)
        if not id in data["guilds"][str(ctx.message.guild.id)][f"{type}_list"]:
            await db(ctx, data, type, id)
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)
    else:
        await ctx.send("Syntax:\n```^add [manga/anime] [id]```")

async def db(ctx, data, type, id):
    if type == "manga":
        if not 'does not exist' in requests.get(f"http://mangadex.org/title/{id}").text:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].append(id)
            if not id in data[type]:
                data["manga"][id] = {"title":"", "ch":"", "chtitle":"", "url":"", "image":""}
            await ctx.send(f"Successfully added {id}")
        else:
            await ctx.send("Invalid MangaDex ID")
    if type == "anime":
        if requests.get(f"http://4anime.to/title/{id}").status_code < 400:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].append(id)
            if not id in data[type]:
                data["anime"][id] = {"ep":"", "title":"", "image":""}
            await ctx.send(f"Successfully added {id}")
        else:
            await ctx.send("Invalid 4anime ID.")

@client.command()
async def remove(ctx, type = None, id = None):
    if type and id:
        with open("data.json") as f:
            data = json.load(f)
        try:
            data["guilds"][str(ctx.message.guild.id)][f"{type}_list"].remove(str(id))
        except ValueError:
            await ctx.send(f"{id} not in {type} list")
        with open("data.json", "w") as f:
            await ctx.send(f"Successfully removed {id}")
            json.dump(data, f, indent=4)

@client.command()
async def list(ctx, type = None):
    with open("data.json") as f:
        data = json.load(f)
    if type:
        await ctx.send("```\n" + str(data["guilds"][str(ctx.message.guild.id)][f"{type}_list"]) + "\n```")
    else:
        await ctx.send("Syntax:\n```^list [manga/anime]```")

@client.command()
async def config(ctx, arg = None):
    with open("data.json") as f:
        data = json.load(f)
    if not arg:
        if str(ctx.message.guild.id) in data["guilds"]:
            await ctx.send("dongman-bot is configured for this server.")
        else:
            data["guilds"][str(ctx.message.guild.id)] = {"channels":[str(ctx.message.channel.id)], "manga_list":[], "anime_list":[]}
            await ctx.send("Server added to dongman-bot.")
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@client.command()
async def move(ctx):
    with open("data.json") as f:
        data = json.load(f)
    data["guilds"][str(ctx.message.guild.id)]["channels"].pop(0)
    data["guilds"][str(ctx.message.guild.id)]["channels"].append(str(ctx.message.channel.id))
    await ctx.send("Notifications will be sent in this channel.")
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

client.run('NzY4NDg2MDYwMDU3MTY1ODQ0.X5BKag._jNselyxwMS1EALuK3rhVWXvnoA')

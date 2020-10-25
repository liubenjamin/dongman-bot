import asyncio
import json
import discord
import filecmp
import shutil
import requests
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

client = commands.Bot(command_prefix = '^')

@client.event
async def on_ready():
    print('ready')
    await client.change_presence(activity = discord.Activity(name = "for new chapters", type = discord.ActivityType.watching))
    client.guild = client.get_guild(697997529312133220)
    client.channel = client.guild.get_channel(697997529312133223)
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
        with open("current", "w") as c:
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

@client.command()
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
                await client.get_channel(data["guilds"][guild]["channels"][0]).send(embed=embed)

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
        with open("current", "w") as c:
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
                await client.get_channel(data["guilds"][guild]["channels"][0]).send(embed=embed)

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
async def ok(ctx):
    await ctx.send('OK')

@client.command()
async def sendjson(ctx):
    with open('data.json') as f:
        a = "```\n"
        a += f.read()
        a += "```"
        await ctx.send(a)

client.run('NzY4NDg2MDYwMDU3MTY1ODQ0.X5BKag.vOlNtGte0zlOapdlkgxWP-JDqV8')

import asyncio
import json
import discord
import time
import filecmp
import shutil
import requests
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from datetime import datetime

client = commands.Bot(command_prefix = '^')

@client.event
async def on_ready():
    print('ready')
    await client.change_presence(activity = discord.Activity(name = "for new chapters", type = discord.ActivityType.watching))
    client.guild = client.get_guild(697997529312133220)
    client.channel = client.guild.get_channel(697997529312133223)
    check.start()

@tasks.loop(seconds=60)
async def check():
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
            if ch != data["manga"][id]:
                data["manga"][id] = ch
                data["new"].append(id)

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@client.command()
async def ok(ctx):
    await ctx.send('OK')

client.run('NzY4NDg2MDYwMDU3MTY1ODQ0.X5BKag.vOlNtGte0zlOapdlkgxWP-JDqV8')

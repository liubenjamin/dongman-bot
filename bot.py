import asyncio
import discord
import time
import filecmp
import shutil
import urllib.request, urllib.error, urllib.parse
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
    url = 'https://manganelo.com/manga/kaguyasama_wa_kokurasetai_tensaitachi_no_renai_zunousen'
    r = urllib.request.Request(url, data = None, headers = {'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(urllib.request.urlopen(r).read().decode('utf-8'), "html.parser")
    with open("current", "w") as c:
        for li in soup.find_all("li"):
            c.write(li.find("a").get('href') + "\n")
    if not filecmp.cmp('current', 'past'):
        with open("current") as c:
            await client.channel.send("new chapter! read it here: " + c.readline())
        shutil.move('current', 'past')
    print("checked at")
    print(datetime.now().time())

@client.command()
async def ok(ctx):
    await ctx.send('OK')

client.run('NzY4NDg2MDYwMDU3MTY1ODQ0.X5BKag.vOlNtGte0zlOapdlkgxWP-JDqV8')

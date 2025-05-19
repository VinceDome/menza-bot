import subprocess, time, discord
from tokens.secret_token import *
from discord.ext import commands, tasks

client = commands.Bot(command_prefix="!", case_insensitive = True, intents=discord.Intents.all())
client.remove_command("help")
dev_id = 810910872792596550
bot_id = 826458615027597343



@client.event
async def on_ready():
    print(f'{client.user} as manager active!')
    
@client.command()
async def start(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    proc = subprocess.Popen(["python", "main.py"])
    
    await ctx.send("started menzabot")

@client.command()
async def stop(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    proc.terminate()
    
    await ctx.send("stopped menzabot")

@client.command()
async def crash(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    proc.terminate()
    await ctx.send("stopped menzabot, exiting...")
    exit(0)
    



client.run(MENZA_TOKEN)

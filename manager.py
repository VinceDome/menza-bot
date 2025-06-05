import subprocess, discord, os
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
    try:
        proc.terminate()
        await ctx.send("stopped menzabot")
    except:
        await ctx.send("menzabot already stopped")    

@client.command()
async def crash(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    msg = ""
    try:
        proc.terminate()
        msg += "stopped menzabot,  "
    except:
        msg += "menzabot already stopped,  "
    msg += "exiting...."

    await ctx.send(msg)
    exit(0)

@client.command()
async def restart(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    msg = ""
    try:
        proc.terminate()
        msg += "stopped menzabot,  "
    except:
        msg += "menzabot already stopped,  "

    msg += "restarting systemmd...."

    await ctx.send(msg)
    os.system("systemctl restart menzabot.service")

@client.command()
async def shutdown(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None
    
    if os.name == "posix":
        msg = ""
        try:
            proc.terminate()
            msg += "stopped menzabot,  "
        except:
            msg += "menzabot already stopped,  "

        msg += "shutting down...."
        await ctx.send(msg)
        os.system("shutdown -h now")
    else:
        await ctx.send("can only shutdown on linux")

@client.command()
async def sync(ctx):
    if ctx.author.id != dev_id:
        return None
    msg = ""
    try:
        proc.terminate()
        msg += "stopped menzabot,  "
    except:
        msg += "menzabot already stopped,  "
    
    msg += "syncing menzabot code..."

    await ctx.send(msg)
    os.system("sudo -u vincedome ./refresh.sh")
    

client.run(MENZA_TOKEN)
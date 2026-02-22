import subprocess, discord, os
from tokens.secret_token import *
from discord.ext import commands, tasks
from discord.ui import Button, View


client = commands.Bot(command_prefix="!", case_insensitive = True, intents=discord.Intents.all())
client.remove_command("help")
dev_id = 810910872792596550
bot_id = 826458615027597343


proc = None
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
        proc = None
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

@client.command(aliases=["commands"])
async def help(ctx):
    if ctx.author.id != dev_id:
        return None
    await ctx.send("***Commands***\n!start\n!stop\n!crash\n!restart --- *(restarts systemmd)*\n!shutdown --- (*the computer*)\n!sync --- (*fetch new code*)\n!help")

@client.command(aliases=["do", "f", "c", ".", ""])
async def remote(ctx):
    global proc
    if ctx.author.id != dev_id:
        return None

    if proc is None:
        startStop = Button(label="Start", style = discord.ButtonStyle.green, emoji = "▶")
    else:
        startStop = Button(label="Stop", style = discord.ButtonStyle.red, emoji = "⏸")

    restart = Button(label="Restart", style = discord.ButtonStyle.blurple, emoji = "🔄")
    shutdown = Button(label="Shutdown", style = discord.ButtonStyle.red, emoji = "🛑")
    sync = Button(label="Sync", style = discord.ButtonStyle.blurple, emoji = "🔁")

    async def startStop_callback(interaction):
        if proc is None:
            await start(ctx)
        else:
            await stop(ctx)
    async def restart_callback(interaction):
        await restart(ctx)
    async def shutdown_callback(interaction):
        await shutdown(ctx)
    async def sync_callback(interaction):
        await sync(ctx)

    startStop.callback = startStop_callback
    restart.callback = restart_callback
    shutdown.callback = shutdown_callback
    sync.callback = sync_callback

    view = View()
    view.add_item(startStop)
    view.add_item(restart)
    view.add_item(sync)
    view.add_item(shutdown)

    await ctx.send("Command remote xd", view=view)

    


client.run(MENZA_TOKEN)
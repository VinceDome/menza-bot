import os, discord, time, random, asyncio, math
from datetime import datetime, timedelta
from discord.ext import commands, tasks

from tokens.secret_token import *
from backend import *

client = commands.Bot(command_prefix=".", case_insensitive = True, intents=discord.Intents.all())
client.remove_command("help")
dev_id = 810910872792596550


@client.event
async def on_ready():
    global today

    print(f'{client.user} active!')
    activity = discord.Game(name="with today's lunch.", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)
    refresher.start()
    

@client.command()
async def lunch(ctx, which=None):
    if GetFood() == "No food ordered for today":
        SyncFood()
    
    await ctx.send(GetFood(date=which))

@client.command()
async def sync(ctx):
    await ctx.send(f"Synced:\n {SyncFood()}")

@tasks.loop(minutes=20)
async def refresher():
    #food reminder for today
    with open(os.getcwd()+"/data/remind.txt", "r") as f:
        history = f.read().rstrip()
    
    if datetime.strptime(history, '%Y.%m.%d').date() < datetime.now().date():
        if datetime.now().hour >= 10:

            if GetFood() == "No food ordered for today":
                SyncFood()
            
            user = await client.fetch_user(int(dev_id))
            msg_dm = await user.create_dm()
            await msg_dm.send(GetFood())

            with open(os.getcwd()+"/data/remind.txt", "w") as f:
                f.write(str(datetime.now().strftime("%Y.%m.%d")))

    #order reminder
    nextdate = datetime.now().date() + timedelta(days=1)
    if nextdate.isoweekday() in set((6, 7)):
        nextdate += timedelta(days=8-nextdate.isoweekday())


        
    


    with open(os.getcwd()+"/data/order.txt", "r") as f:
        order = f.read().rstrip()
    
    if datetime.strptime(order, '%Y.%m.%d').date() < datetime.now().date():
        for i in range(2):
            nextfood = GetFood(nextdate.strftime("%Y.%m.%d"))
            if nextfood == "No food ordered for today":
                #only refresh the first time
                if i == 0:
                    SyncFood()
            else:
                #exit if there is food ordered
                return
        
        user = await client.fetch_user(int(dev_id))
        msg_dm = await user.create_dm()
        await msg_dm.send(f"""Reminder to order food for {nextdate.strftime("%Y.%m.%d")}""")

        with open(os.getcwd()+"/data/order.txt", "w") as f:
            f.write(str(datetime.now().strftime("%Y.%m.%d")))
    


    
    


@client.event
async def on_message(message):
    
    if message.author == client.user:
        return

    print(f"""{message.author} in {message.guild} #{message.channel} sent "{message.content}" """)



    
    if message.content.startswith("ping"):
        await message.channel.send(f"pong ({round(client.latency*1000)}ms)")
        print("-----------------------\nreplied to ping\n-----------------------")

    
    await client.process_commands(message)


client.run(MENZA_TOKEN)
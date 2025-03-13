import os, discord, time, random, asyncio, math
from datetime import datetime, timedelta
from discord.ext import commands, tasks

from tokens_new.secret_token import *
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
    if GetFood(user=ctx.author.id) == "No food ordered for today":
        SyncFood()

    await ctx.send(GetFood(user=ctx.author.id, date=which))

@client.command()
async def sync(ctx):
    if ctx.author.id != dev_id:
        return None
    
    await ctx.send(f"Synced:\n {SyncFood()}")

@client.command()
async def join(ctx, *, name):
    if AddUser(ctx.author.id, name):
        await ctx.send(f"""Succesfully recieving notifications for [{name}]""")
    else:
        await ctx.send(f"Already subscribed to [{GetUsers()[ctx.author.id]}]")
   
@client.command()
async def help(ctx):
    await ctx.send("Auto-forward the original lunch messages to here: vincespanol@gmail.com, then type:\n.join [name] <-- your official name which appears in the emails")
   

@tasks.loop(minutes=20)
async def refresher():
    #food reminder for today
    for id in GetUsers():
        
        user = GetUsers()[id]
       
        with open(f"data/{user}/remind.txt", "r", encoding="utf-8") as f:
            history = f.read().rstrip()
        
        if datetime.strptime(history, '%Y.%m.%d').date() < datetime.now().date():
           
            if datetime.now().hour >= 10:

                if GetFood(user=id) == "No food ordered for today":
                    SyncFood()
                
                userD = await client.fetch_user(id)
                msg_dm = await userD.create_dm()
                await msg_dm.send(GetFood(user=id))
                
                with open(f"data/{user}/remind.txt", "w", encoding="utf-8") as f:
                    f.write(str(datetime.now().strftime("%Y.%m.%d")))

        #order reminder
        nextdate = datetime.now().date() + timedelta(days=1)
        if nextdate.isoweekday() in set((6, 7)):
            nextdate += timedelta(days=8-nextdate.isoweekday())


            
        


        with open(f"data/{user}/order.txt", "r") as f:
            order = f.read().rstrip()
        
        if datetime.strptime(order, '%Y.%m.%d').date() < datetime.now().date():
            for i in range(2):
                nextfood = GetFood(user=id, date=nextdate.strftime("%Y.%m.%d"))
                if nextfood == "No food ordered for today":
                    #only refresh the first time
                    if i == 0:
                        SyncFood()
                else:
                    #exit if there is food ordered
                    return
            
            userD = await client.fetch_user(id)
            msg_dm = await userD.create_dm()
            await msg_dm.send(f"""Reminder to order food for {nextdate.strftime("%Y.%m.%d")}""")

            with open(f"data/{user}/order.txt", "w") as f:
                f.write(str(datetime.now().strftime("%Y.%m.%d")))
        

@client.command()
async def dm(ctx, _id, *, message):
    if ctx.author.id != dev_id:
        return None
    if "<@" in _id:
        _idL = list(_id)
        try:
            for i in ["@", "<", ">", "!"]:
                _idL.remove(i)
        except ValueError:
            pass

        _id = int("".join(_idL))
    user = await client.fetch_user(int(_id))
    msg_dm = await user.create_dm()
    await msg_dm.send(message)
    await ctx.send(f""" "{message}" sent to [{user}]""")
    
    


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
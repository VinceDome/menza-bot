import os, discord, time, random, asyncio, math
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ui import Button, View

from tokens.secret_token import *
from backend import *
from order import *

dev_id = 810910872792596550
bot_id = 826458615027597343

client = commands.Bot(command_prefix=".", case_insensitive = True, intents=discord.Intents.all())
client.remove_command("help")

@client.event
async def on_ready():
    global today, session
    session = Login()
  
    print(f'{client.user} active!')
    activity = discord.Game(name="with today's lunch.", type=3)
    await client.change_presence(status=discord.Status.online, activity=activity)
    refresher.start()
    

@client.command()
async def lunch(ctx, og="ai", which=None):
    
    if GetFood(user=ctx.author.id) == "No food ordered for today" and which is None:
        SyncFood()

    if og.lower() == "og":
        og = True
    else:
        og = False
    
    await ctx.send(GetFood(user=ctx.author.id, og=og, date=which))

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
   

class ProgressBar:
    def __init__(self, ctx):
        self.ctx = ctx
    
    async def setup(self):
        self.content = ["Starting..."]
        self.msg = await self.ctx.send(content="\n".join(self.content))
    
    async def update(self, message, view=None):
        self.content.append(message)
        await self.msg.edit(content="\n".join(self.content), view=view)

@client.command()
async def order(ctx, day=1, free=False):
    global session
    

    prog = ProgressBar(ctx)
    await prog.setup()
    
    
    if ctx.author.id not in (dev_id, bot_id):
        return None
    try:
        day = datetime.strptime(day, '%Y.%m.%d')
    except:
        try:
            day = int(day)
        except:
            await prog.update("Invalid date format")
            return None
    
        day = datetime.now() + timedelta(days=day)
        if day.isoweekday() in set((6, 7)):
            day += timedelta(days=8-day.isoweekday())
        

   
    await prog.update("Fetching menu...")

    data, session = GetMenu(session, day)
    
    favs = [0, 1, 2, 3, 4, 7]
    def ChangeView(change=None, mode=False):
        global buttons, view
        if change is None:
            soup1 = Button(label=data[favs[0]].text, style = discord.ButtonStyle.gray, emoji = "🍲")
            soup2 = Button(label=data[favs[1]].text, style = discord.ButtonStyle.gray, emoji = "🍲")
            main1 = Button(label=data[favs[2]].text, style = discord.ButtonStyle.gray, emoji = "🍝")
            main2 = Button(label=data[favs[3]].text, style = discord.ButtonStyle.gray, emoji = "🍝")
            main3 = Button(label=data[favs[4]].text, style = discord.ButtonStyle.gray, emoji = "🍝")
            street = Button(label=data[favs[5]].text, style = discord.ButtonStyle.gray, emoji = "🍔")
            preference = Button(label="Add to preference", style = discord.ButtonStyle.green, emoji = "⭐")
            confirm = Button(label="Confirm", style = discord.ButtonStyle.green, emoji = "✅")
            buttons = [soup1, soup2, main1, main2, main3, street, preference, confirm]

        buttons[0].callback = soup1_call
        buttons[1].callback = soup2_call
        buttons[2].callback = main1_call
        buttons[3].callback = main2_call
        buttons[4].callback = main3_call
        buttons[5].callback = street_call
        buttons[6].callback = preference_call
        buttons[7].callback = confirm_call

        

        if change is not None:
            print(change)
            if mode == "select":
                buttons[change].style = discord.ButtonStyle.blurple
            elif mode == "deselect":
                buttons[change].style = discord.ButtonStyle.gray
            else:
                for i in buttons:
                    if i.style == discord.ButtonStyle.blurple:
                        i.style = discord.ButtonStyle.red


        view = View()
        for i in buttons:
            view.add_item(i)
        

    staged = []
    async def check(interaction, index):
        selected = data[favs[index]]
        if selected in staged:
            staged.remove(selected)
            ChangeView(change=index, mode="deselect")
        else:
            staged.append(selected)
            ChangeView(change=index, mode="select")
        await interaction.response.edit_message(view=view)

    async def soup1_call(interaction):
        await check(interaction, 0)
    async def soup2_call(interaction):
        await check(interaction, 1)
    async def main1_call(interaction):
        await check(interaction, 2)
    async def main2_call(interaction):
        await check(interaction, 3)       
    async def main3_call(interaction):
        await check(interaction, 4)
    async def street_call(interaction):
        await check(interaction, 5)

    async def preference_call(interaction):
        print(f"added {staged} to preference")
        print(staged,  "staged")
        Preference(staged)
        await interaction.response.edit_message(view=view)
        

    async def confirm_call(interaction):
        ChangeView(change=7, mode="end")
        await interaction.response.edit_message(view=view)
        OrderFood(session, staged, free)
    
    await prog.update("Creating view...")

    ChangeView()
    await prog.update("DONE!", view=view)
   

@tasks.loop(minutes=20)
async def refresher():
    global session
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
        

        #get the next date
        nextdate = datetime.now() + timedelta(days=1)
        if nextdate.isoweekday() in set((6, 7)):
            nextdate += timedelta(days=8-nextdate.isoweekday())


        #order reminder
        if datetime.now().hour < 17:
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

                if id == dev_id:
                    menu, session = GetMenu(session, nextdate)
                    
                    preference = Preference()
                    
                    suggested = []
                    
                    if menu[7].text in preference:
                        suggested.append(menu[7].text)
        
                    else:
                        for i in menu:
                            if i.text in preference:
                                suggested.append(i.text)
                                break
                    
                    
                    await msg_dm.send(f"""Reminder to order food for {nextdate.strftime("%Y.%m.%d")}\nSuggested: {"----".join(suggested)}""")
                    
                    
                else:
                    await msg_dm.send(f"""Reminder to order food for {nextdate.strftime("%Y.%m.%d")}""")

                with open(f"data/{user}/order.txt", "w") as f:
                    f.write(str(datetime.now().strftime("%Y.%m.%d")))
        else:
            userD = await client.fetch_user(id)
            msg_dm = await userD.create_dm()

            if id == dev_id:
                menu, session = GetMenu(session, nextdate)
                        
                preference = Preference()
                
                suggested = []
                
                if menu[7].text in preference:
                    suggested.append(menu[7])

                else:
                    for i in menu:
                        if i.text in preference:
                            suggested.append(i)
                            break

                if not suggested == []:
                    OrderFood(session, suggested[0])
                    await msg_dm.send(f"""Ordered food for {nextdate.strftime("%Y.%m.%d")}\nOrdered: {"----".join(i.text for i in suggested)}""")
                else:
                    await msg_dm.send(f"Can't order food for {nextdate.strftime("%Y.%m.%d")}, no preference set")
                    
            
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
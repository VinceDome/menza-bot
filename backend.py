import os.path, base64, shutil
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

from tokens.genai import GOOGLE_KEY

import google.generativeai as genai
from order import Cutoff

genai.configure(api_key=GOOGLE_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")



SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
def SyncFood():
  bigdata = []

  creds = None
  if os.path.exists(os.getcwd()+"/tokens/token.json"):
      creds = Credentials.from_authorized_user_file(os.getcwd()+"/tokens/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.

  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
        
      else:
        
        flow = InstalledAppFlow.from_client_secrets_file(os.getcwd()+"/tokens/credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open(os.getcwd()+"/tokens/token.json", "w") as token:
        token.write(creds.to_json())

  #creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  service = build("gmail", "v1", credentials=creds)
  messages = service.users().messages()


  results = messages.list(userId="me", q="akg@mealplanner.hu").execute()

  #initializing the list which tracks what emails are useless
  users = GetUsers()
  names = {}
  for i in users.values():
    names.update({i:False})

  for i in results["messages"]:
    
    msg = messages.get(userId="me", id=i["id"]).execute()

    for i in msg["payload"]["headers"]:
      if i["name"] == "Subject":
        sub = i["value"]
        break

    print(sub)

    if "Megrendelés" not in sub:
      
      continue

    data = msg["payload"]["parts"][0]["body"]["data"]
    
    #data = bytes(str(data), encoding='utf-8')
    
    data = base64.b64decode(data).decode("utf-8")
    

    
    try:
      hardcode = data.split("ÉtelekMennyiségÖsszeg")
      name = hardcode[0]

      del hardcode[0]
      hardcode.append(hardcode[0].split("Megrendelés értéke:"))
      del hardcode[0]
      for i in hardcode[0]:
        hardcode.append(i)
      del hardcode[0]
      del hardcode[1]
    except:
      continue

    clean = []
    for i in ["\r", "\n"]:
      hardcode[0] = hardcode[0].replace(i, "")

    hardcode = hardcode[0].split("Ft")

    for i in hardcode:
      if i == "":
        continue
      try:
        date = i[:10]
        food_raw = i.split("Ebéd")[1]
        food = Cutoff(food_raw)
      except:
        print("Error in parsing date or food")

      if not date=="" or not food=="":
        clean.append([date, food])
    
    name = name.split("Étkező neve:")[1]
    name = name.split("Intézmény:")[0]
    
    
    for i in ["\n", "\t", "\r", "  "]:
      name = name.replace(i, "")
    if name[0] == " ":
      name = list(name)
      del name[0]
      name = "".join(name)

    print(clean)
    
    if names[name]:
      continue

    #check if it contains food for future dates
    usable = [False, 0]
    for i in clean:
      if datetime.strptime(i[0], '%Y.%m.%d').date() >= datetime.now().date():
        usable = [True, clean.index(i)]
        break

    if usable[0]:
      for i in range(usable[1], len(clean)):
    
          response = model.generate_content(f"Csak az étel kategóriája és a neve legyen feltüntetve az alábbi szövegrészletből. Ne írj ki semmi mást. {clean[i][1]}")
          clean[i].append(response.text)

          clean[i].append(name)

          print(response.text)
          
          bigdata.append(clean[i])
          
    else:
      #if its not usable, then the following emails will be useless as well
      names[name] = True
      if not False in names.values():
        break

    
  for i in users.values():
    with open(f"data/{i}/bigdata.txt", "w", encoding="utf-8") as f:
        pass
    

  for i in bigdata:
    print(i)
    
    with open(f"data/{i[3]}/bigdata.txt", "a+", encoding="utf-8") as f:
      try:
        del i[3]
        f.write("\t".join(i)+"%%%")
      except:
        pass
      pass
    
  joined = []
  print(bigdata)
  for i in bigdata:
    joined.append("\t".join(i))  
  return "\n".join(joined)

def GetFood(user, og=False, date=None):
  if date == None:
    date = datetime.now().date()
  else:
    date = datetime.strptime(date, '%Y.%m.%d').date()

  bigdata = []

  user = GetUsers()[user]  
  
  with open(f"data/{user}/bigdata.txt", "r", encoding="utf-8") as f:
    fR = f.read().rstrip()
    if not fR == "":
      for i in fR.split("%%%"):
        if i != "":
          bigdata.append(i.split("\t"))
      

  deletefrom = None
  for i in range(len(bigdata)-1, -1, -1):
    
    if datetime.strptime(bigdata[i][0], '%Y.%m.%d').date() < datetime.now().date():
      deletefrom = i
      break
    

  if deletefrom is not None:
    for a in range(i+1):
      del bigdata[0]

  
  with open(f"data/{user}/bigdata.txt", "w+", encoding="utf-8") as file:
      for i in bigdata:
        file.write("\t".join(i)+"%%%")

  final = []
  for i in bigdata:
    if datetime.strptime(i[0], '%Y.%m.%d').date() == date:
      final.append(i)

  if final == []:
    final = "No food ordered for today"
  else:
    if og:
      num = 1
    else:
      num=2

    rand = []
    for i in final:
      rand.append(i[num])
    final = "\n".join(rand)


  
  return final

def GetUsers():
  users = {}
  try:
    with open("data/users.txt", "r", encoding="utf-8") as f:
      for i in f.read().split("\n"):
        i = i.split("\t")
        users.update({int(i[0]):i[1]})
  except:
    pass
  return users
      
def AddUser(id, user):
  users = GetUsers()

  if id not in users:
    users.update({id:user})

    #update user file
    with open("data/users.txt", "w+", encoding="utf-8") as f:
      for i in users.items():
        print(i)
        f.write(str(i[0])+"\t"+i[1])

      if i != list(users.items())[-1]:
        f.write("\n")
    
    
    #create their directory
    os.mkdir(f"data/{user}")
    for i in ["remind", "order", "autoorder"]:
      with open(f"data/{user}/{i}.txt", "a+") as f:
        f.write("2025.01.01")
        pass

    with open(f"data/{user}/bigdata.txt", "w+") as f:
      pass

    return True
  else:
    return False

def RemoveUser(id):
  users = GetUsers()

  if id in users:
    #remove their directory
    shutil.rmtree(f"data/{users[id]}")
    del users[id]

    #update user file
    with open("data/users.txt", "w+", encoding="utf-8") as f:
      for i in users.items():
        f.write(str(i[0])+"\t"+i[1])
        if i != list(users.items())[-1]:
          f.write("\n")  

    return True
  else:
    return False

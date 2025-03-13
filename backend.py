import os.path, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

from tokens_new.genai import GOOGLE_KEY

import google.generativeai as genai

genai.configure(api_key=GOOGLE_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")



SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def SyncFood():
  bigdata = []

  creds = None
  if os.path.exists(os.getcwd()+"/tokens_new/token.json"):
      creds = Credentials.from_authorized_user_file(os.getcwd()+"/tokens_new/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.

  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        
        
      else:
        
        flow = InstalledAppFlow.from_client_secrets_file(os.getcwd()+"/tokens_new/credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open(os.getcwd()+"/tokens_new/token.json", "w") as token:
        token.write(creds.to_json())

  #creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  service = build("gmail", "v1", credentials=creds)
  messages = service.users().messages()


  results = messages.list(userId="me", q="akg@mealplanner.hu").execute()

  users = ReadUsers()
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
    hardcode = hardcode[0].split("Ft")

    for a in hardcode:
      date = ""
      food = ""
      for i in range(len(a)):
  
        if i < 10:
          date = date+a[i]
          
        else:
          food = food+a[i]

      if not date=="" or not food=="":
        clean.append([date, food])
    
    name = name.split("Étkező neve:")[1]
    name = name.split("Intézmény:")[0]
    
    
    for i in ["\n", "\t", "  ", "\r"]:
      name = name.replace(i, "")

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
          """
          already = False
          for a in bigdata:
            
            if clean[i] == a:
              already = True
              break
          if not already:
          """
          
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
    try:
      os.remove(f"data/{i}/bigdata.txt")
    except:
      pass
    

  for i in bigdata:
    print(i)
    try:
      with open(f"data/{i[3]}/bigdata.txt", "a+", encoding="utf-8") as f:
        del i[3]
        f.write("\t".join(i)+"%%%")
    except:
      pass


  """
  with open(os.getcwd()+"/data/bigdata.txt", "w+", encoding="utf-8") as file:
      for i in bigdata:
        file.write("\t".join(i)+"%%%")
  """
  joined = []
  print(bigdata)
  for i in bigdata:
    joined.append("\t".join(i))  
  return "\n".join(joined)
  
  """
  for i in bigdata:
    if datetime.strptime(i[0], '%Y.%m.%d').date() == datetime.now().date():
      return "----------------".join(i)
  """

def GetFood(user, date=None):
  if date == None:
    date = datetime.now().date()
  else:
    date = datetime.strptime(date, '%Y.%m.%d').date()

  bigdata = []

  user = GetUsers()[user]

  with open(f"data/{user}/bigdata.txt", "r", encoding="utf-8") as f:
    fR = f.read().rstrip()
    if not fR == "":
      temp = fR.split("%%%")
      

      for i in temp:
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
    """
    rand = []
    for i in final:
      rand.append("\t".join(i))
      
    print(final)
    final = "\n".join(rand)
    """
    rand = []
    for i in final:
      rand.append(i[2])
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
    
    #create their directory
    os.mkdir(f"data/{user}")
    for i in {"remind", "order"}:
      with open(f"data/{user}/{i}.txt", "a+") as f:
        f.write("2025.01.01")
        pass

    return True
  else:
    return False



import os.path, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

import google.generativeai as genai
GOOGLE_KEY = "AIzaSyAixO4lbWLu7-CV4_2bCtEzO056jQ3HVp0"
genai.configure(api_key=GOOGLE_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


API_KEY = "AIzaSyAixO4lbWLu7-CV4_2bCtEzO056jQ3HVp0"
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
          print(response.text)
          
          bigdata.append(clean[i])
          
    else:
      #if its not usable, then the following emails will be useless as well
      break
    
  
  with open(os.getcwd()+"/data/bigdata.txt", "w+", encoding="utf-8") as file:
      for i in bigdata:
        file.write("\t".join(i)+"%%%")

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

def GetFood(user="Bartha Vince Döme", date=None):
  if date == None:
    date = datetime.now().date()
  else:
    date = datetime.strptime(date, '%Y.%m.%d').date()

  bigdata = []
  with open(os.getcwd()+"/data/bigdata.txt", "r", encoding="utf-8") as f:
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

  
  with open(os.getcwd()+"/data/bigdata.txt", "w+", encoding="utf-8") as file:
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



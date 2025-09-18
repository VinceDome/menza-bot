import requests, json, random
from bs4 import BeautifulSoup
from tokens.ssocreds import *
from datetime import datetime, timedelta


def ExtractMenu(soup):
    data = [[] for i in range(5)]
    #shifted the days so we skip the first bar
    current_day = -1-5
    
    
    for i in soup.find_all("div", class_=lambda x: x in ["mealplanner-menu-cell--head-date", "mealplanner-menu-cell-food"]):
        
        if i["style"] == "order:0;":
            current_day += 1
            if current_day > 4:
                break
            continue
        elif i["style"] == "order:1;":
            continue
        
        if current_day >= 0:
            data[current_day].append(i)
        
    return data

def Login():
    etelrendelesURL = "https://etelrendeles.akg.hu/" # original site
    requestURL = "https://sso.akg.hu/identity_provider.php?authnrequest" #send ETELRENDELES token here to access login site
    identityURL = "https://sso.akg.hu/identity_provider.php" #send login creds here
    responseURL = "https://etelrendeles.akg.hu/provider/service_provider.php?authnresponse" #send login token here

    #initializing session
    session = requests.Session()

    #retrieve ETELRENDELES token to access login site
    response = session.get(etelrendelesURL)
    soup = BeautifulSoup(response.text, "html.parser")
    token = soup.find("input", {"name": "Request"})["value"]
    ETELRENDELES = {"Request":token}

    #enter login site with token
    session.post(requestURL, data=ETELRENDELES)

    #send login and retrieve login token
    response = session.post(identityURL, data=credentials)
    soup = BeautifulSoup(response.text, "html.parser")
    value = soup.find("input", {"name": "Response"})["value"]
    LOGIN = {"Response":value}

    #send login token to RESPONSE checker == log in
    session.post(responseURL, data=LOGIN)
    #soup = BeautifulSoup(response.text, "html.parser")

    return session

def GetMenu(session, day):
    biaURL = "https://etelrendeles.akg.hu/bia-ebed-rendeles"
    
    response = session.get(biaURL)
    soup = BeautifulSoup(response.text, "html.parser")

    #find the current week
    current_year = datetime.now().strftime("%Y")
    selected = soup.find_all("option", {"data-year":current_year,  "selected":True})
    selected = [selected[0]["value"], selected[0]["data-date1"], selected[0]["data-date2"]]
    
    bia_dates = soup.find_all("option", {"data-year":current_year})
    bia_dates.reverse()

    for i in bia_dates:
        if day.date() > datetime.strptime(i["data-date2"], '%Y-%m-%d').date():
            break
        week = [i["value"], i["data-date1"], i["data-date2"]]

    if not week == selected:
        print("performing date change")
        #set url, perform date change
        datechangeurl = f"https://etelrendeles.akg.hu/index.php?page=bia-het-valtas&c=1&week={week[0]}&year={current_year}&date1={week[1]}&date2={week[2]}&p=bia-ebed-rendeles"
        response = session.get(datechangeurl)
        soup = BeautifulSoup(response.text, "html.parser")

    data = ExtractMenu(soup)
    
    return data[day.isoweekday()-1], session

def OrderFood(session, meals, free):
    selectURL = "https://etelrendeles.akg.hu/index.php?c=1&page=bia-ebed-rendeles&mode=save"
    biaURL = "https://etelrendeles.akg.hu/bia-ebed-rendeles"
    feladasURL = "https://etelrendeles.akg.hu/bia-megrendeles-feladasa"
    payURL = "https://etelrendeles.akg.hu/index.php?page=bia-megrendeles-feladasa&c=1&mode=save&paying=balance"
    
    

    order_data = []
    for i in meals:
        inp = i.label.input
        if free:
            price = "MC4wMDAw"
        else:
            price = inp["data-f"]

        order_data.append({
                "menuid": inp["data-menuid"],
                "info": inp["data-info"],
                "mealid": inp["data-mealid"],
                "quantity": 1,
                "date": inp["data-date"],
                "price": price
            })
        
    #add the new menu item which is required to give it a price lmao
    order_data.append({"menuid": "501", "info": "bc49D8IgEAbg/3Jza44aP+pMjSZ+LW4uCKSSkCPBMhn/uxztpDLdPXnfcC+QarCwgQabRY1tLQRUcLSUulPWQyL9mGB3zdDdbwnRtqag8l8p5X9TyhEjJe/HjTvjdolOl8/niDPMDybbS9bVcp0hlgOxgnN0vaN/HemeOiQaMvP52xBMHoErxkYOC3h/AA==", "mealid": "3", "quantity": 1, "date": inp["data-date"], "price": "MjMwMC4wMDAw"})

    order_data = {
        "data": json.dumps(order_data)
    }

    """
    order_data = {
        "data": json.dumps([
            {
                "menuid": inp["data-menuid"],
                "info": inp["data-info"],
                "mealid": inp["data-mealid"],
                "quantity": 1,
                "date": inp["data-date"],
                "price": zero_code#inp["data-f"]
            }
        ])
    }
    """

    print(order_data)

    response = session.post(selectURL, data=order_data)
    print(response)
    print(response.text)

    #response = session.get(biaURL)

    #feladás
    response = session.get(feladasURL)
    print(response.text)

    #fizetés
    response = session.get(payURL)
    print(response.text)

def Preference(data=None):
    preferencePath = "data/preference.txt"
    
    with open(preferencePath, "r", encoding="utf-8") as f:
        savedPreference = f.read().split("%%%")
    if savedPreference == [""]:
        savedPreference = []

    if data is None:
        return savedPreference
    else:
        data = [Cutoff(i.text) for i in data]
        
        for i in data:
            if i not in savedPreference:
                savedPreference.append(i)
            else:
                savedPreference.remove(i)

        
        print(savedPreference)
        with open(preferencePath, "w", encoding="utf-8") as f:
            f.write("%%%".join(savedPreference))
        
#! still doesn't recommend correct food (menu not working, doesN't know to order soup too)
def GetSuggested(menu):
    preference = Preference()            
    suggested = []
    
    #4 = soup
    #5 = salad
    #6, 7, 8, 9 = main course
    clean = Cutoff(menu[7].text)

    #if street food is in preference, it takes priority
    if clean in preference:
        return menu[7]
    else:
        #add all preferred items to suggested
        for i in menu:
            clean = Cutoff(i.text)
    
            if clean in preference:
                suggested.append(i)
        
        #sort the suggested items into soup and main course
        soup = []
        main = []
        for i in suggested:
            if i["style"] in ["order:4;", "order:5;"]:
                soup.append(i)
            elif i["style"] in ["order:6;", "order:7;", "order:8;", "order:9;"]:
                main.append(i)
        
        #if either soup or main is empty, return False because we will order only if it's sure
        if len(soup) == 0 or len(main) == 0:
            return []
        else:
            return (random.choice(soup), random.choice(main))

def Cutoff(string):
    #cut off the string at the first number or punctuation
    clean = ""
    for a in string:
        if a in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", ".", ","]:
            break
        clean += a
    return clean
# load in all foods and its appropriate data
# make the user select one //// develop a ranking system
# make user give ok command
# order the food

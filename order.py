import requests, json, os
from bs4 import BeautifulSoup
from tokens.ssocreds import *
from datetime import datetime, timedelta

with open("data/preference.txt", "a+") as f:
    pass

def ExtractMenu(soup):
    data = [[] for i in range(5)]
    current_day = -1
    first_checker = "nem"

    for i in soup.find_all("div", {"class":"mealplanner-menu-cell"}):
        

        if i["style"] == "order:0;":
            #if this is the first order:0, it's the header
            if first_checker == "nem":
                first_checker = False
                continue
            
            #if we reach another order:0, it's the first  day
            elif not first_checker:
                first_checker = True
                

            #it's the next day
            current_day +=1
            continue
        elif i["style"] == "order:1;":
            continue

        #if the variable is false, it means we're in the header
        if not first_checker:
            continue

        
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

    response = session.get(biaURL)
    soup = BeautifulSoup(response.text, "html.parser")

    data = ExtractMenu(soup)
    

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
        data = [i.text for i in data]

        
        for i in data:
            if i not in savedPreference:
                savedPreference.append(i)
            else:
                savedPreference.remove(i)

        os.remove(preferencePath)
        print(savedPreference)
        with open(preferencePath, "w+", encoding="utf-8") as f:
            f.write("%%%".join(savedPreference))
        

# load in all foods and its appropriate data
# make the user select one //// develop a ranking system
# make user give ok command
# order the food

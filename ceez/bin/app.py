from flask import Flask, request
import json, os
from bin.bot import Bot
from subprocess import Popen

#creating webhook url to fetch alert from tradingview 
app = Flask(__name__) 
with open('usr/credentials.json') as f: 
    creds = json.load(f) 
    f.close() 

with open('usr/settings.json') as f: 
    settings = json.load(f) 
    f.close() 

with open('usr/alert.json') as f: 
    alert = json.load(f) 
    f.close() 

# Creating bot instance 
Bot1 = Bot(creds=creds, settings=settings) 
#Bot started in thread 
Bot1.start()
print("seeeeeeeeeeeeee") 

def take_response(): 
    if input() == '': 
        try:
            with open('usr/settings.json') as f: 
                settings = json.load(f) 
                f.close() 
            Bot1.update_attributes(settings=settings) 
            print("\n\tParameters updated!!\t\n") 
            #take_response()
        except: 
            print('Invalid inputs, check the settings.json') 
            take_response() 
    else:
        print('Enter valid input')
        take_response()

@app.route('/webhook', methods = ['POST'])
def Alert():
    #fetching data from webhook url
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode('utf-8'))
            print(data)
            global alert

            if (alert['passcode']==data['passcode']):
                alert=data

                if bool(settings['auto_trade']):
                    Bot1.read_alert(alert)
                    print('alert sent') 
                else: 
                    print('Alert received from webhoook please update settings.\n') 
                    val = input("Do you want to take this trade(y/n): ")
                    if val in ['y','Y']:
                        val = input("Do you want to update settings(y/n): ")
                        if val in ['y','Y']:
                            Popen('python run.py')
                        else:
                            pass 
                        take_response()
                        Bot1.read_alert(alert)   
                        print('alert sent')  
                    else:
                        print('You cancelled this trade.\n')

            else :
                print("error") 
            return data 
        except Exception as e:
            print(e)

if __name__ == '__main__':
    app.run(port=80)
#Python libraries that we need to import for our bot
import os
import random
from flask import Flask, request
from pymessenger.bot import Bot
import psycopg2
import datetime

app = Flask(__name__)
DATABASE_URL = os.environ['DATABASE_URL']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
bot = Bot(ACCESS_TOKEN)
 
#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])

def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
       output = request.get_json()
       for event in output['entry']:
          messaging = event['messaging']
          for message in messaging:
            if message.get('message'):
                #Facebook Messenger ID for user so we know where to send response back to
                recipient_id = message['sender']['id']
                message_text = message['message']['text']
                
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO chat_log VALUES (%s, %s, %s, %s)", (recipient_id,"Stevie",""+message_text+"",datetime.datetime.now()))
                    conn.commit()
                except:
                    pass
                
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO user_features VALUES (%s, %s)  ON CONFLICT (uid) DO NOTHING ", (recipient_id,datetime.datetime.now()))
                    conn.commit()
                except:
                    pass
                    
                if message['message'].get('text'):
                    response_sent_text = get_message(message_text,conn)
                    send_message(recipient_id, response_sent_text)
                    
                    cur = conn.cursor()
                    cur.execute("INSERT INTO chat_log VALUES (%s, %s, %s, %s)", ("Stevie", recipient_id,""+response_sent_text+"",datetime.datetime.now()))
                    conn.commit()
                
                #if user sends us a GIF, photo,video, or any other non-text item
                if message['message'].get('attachments'):
                    response_sent_nontext = get_message(message_text,conn)
                    send_message(recipient_id, response_sent_nontext)
                                            
    return "Message Processed"
 
def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'
    #return one
 
#chooses a random message to send to the user
def get_message(message_text,conn):
    greetings = ['Привет', 'привет', 'Здарово', 'здарово']
    question = ['Что идет в кино?','Что идёт в кино?','Что в кино?','Что посмотреть?','Давай']
    if message_text in greetings: 
        responses = ['Привет!','Салют!','Сто лет тебя не видел)']
        response = random.choice(responses)
    elif message_text in question:
        cur = conn.cursor()
        cur.execute("select * from premieres ORDER BY random()")
        row = cur.fetchone()
        response ="Иди посмотри "+row[1]+" "+row[2]
    else:
        responses = ["Сорян, братан, я не понял", "Ты много от меня хочешь :)", "Спроси меня лучше, что идет в кино", "Воу воу воу полегче!", "Давай поговорим о кино"]
        response = random.choice(responses)
    return response
 
#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

if __name__ == "__main__":
    app.run()
    
#cur.close()
#conn.close()    
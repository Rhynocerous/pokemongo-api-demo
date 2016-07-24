from twilio.rest import TwilioRestClient

account_sid = "AC7b5bc00ad365261d5698c1fe64365be5" # Your Account SID from www.twilio.com/console
auth_token  = "993bb5e87a1b5e1c30c9f10ad7725bc7"  # Your Auth Token from www.twilio.com/console



class Notifications:
    def __init__(self,account_sid, auth_token, num):
        self.client = TwilioRestClient(account_sid, auth_token)
        self.num = num

        
    def send_messages(self,poke,users):
        global twil
        for user in users:
            if poke.name in user['wantlist']:
                self.send(poke,user['number'])

    def send(self,poke,to_num):
	try:
            text = "{n} found until {t}\nhttps://www.google.com/maps/place/{lat},{lon}".format(n=poke.name,
                                                    t=poke.vanish_time,lat = poke.coords[0],lon = poke.coords[1])
            message = self.client.messages.create(body=text,to=to_num,from_=self.num)
            temp = message
	except:
            return

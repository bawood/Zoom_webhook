from ast import Str
import json
from telnetlib import IP
from flask import Flask, Response, request
from flask_mysqldb import MySQL

import socket
application = Flask(__name__)

application.config.from_prefixed_env()
mysql = MySQL(application)

def reverseLookup(IP):
	try:
		return socket.gethostbyaddr(IP)[0].lower()
	except Exception:
		return IP

@application.route('/hello')
def hello_world():
   return 'Hello World'

@application.route('/device_registration/', methods = ['POST'])
def zoomphone_registration():
   token = request.headers.get('authorization', type=str)
   if token == application.config["ZOOM_TOKEN"]:
      print("device registration webhook received from: ", reverseLookup(request.remote_addr))
      if request.is_json:
         data = request.get_json()
# sample event:
# {"event": "phone.device_registration",
#  "payload": {"account_id": "sghqeuivblevhfvafvbavfn", 
#              "object": {"device_id": "VWt3quhfvasdna",
#                         "device_name": "123456779",
#                         "mac_address": "19878175118f"}},
#  "event_ts": 1666801622748}
         if data:
            device_id = data['payload']['object']['device_id']
            mac_address = data['payload']['object']['mac_address']
            print("device_id: ", device_id, " mac_address: ", mac_address)
            like_phone = ("ph_" + mac_address + "%",)
            sql = "SELECT * FROM ZoomPhoneNameFloorRoom WHERE PhoneName LIKE %s"
            try:
               print("mysql_db: " + application.config["MYSQL_DB"])
               cur = mysql.connection.cursor()
               cur.execute(sql, like_phone)
               rv = cur.fetchall()
            except Exception as e:
               print("SQL Exception occurred: ", e)
            if rv:
               for r in rv:
                  print("found result ", r)
      return Response("", 200)
   else:
      print("invalid auth token: ", token, "from host: ", reverseLookup(request.remote_addr))
      return Response("Access denied", 401)

if __name__ == '__main__':
   application.run()
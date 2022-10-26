from ast import Str
import json
from telnetlib import IP
from flask import Flask, Response, request
from flask_mysqldb import MySQL

import socket
app = Flask(__name__)

app.config.from_prefixed_env()

def reverseLookup(IP):
	try:
		return socket.gethostbyaddr(IP)[0].lower()
	except Exception:
		return IP

@app.route('/hello')
def hello_world():
   return 'Hello World'

@app.route('/device_registration/', methods = ['POST'])
def zoomphone_registration():
   token = request.headers.get('authorization', type=str)
   if token == app.config["ZOOM_TOKEN"]:
      print("device registration webhook received from: ", reverseLookup(request.remote_addr))
      if request.is_json:
         if request.json:
            print(json.dumps(request.json))
      return Response("", 200)
   else:
      print("invalid auth token: ", token, "from host: ", reverseLookup(request.remote_addr))
      return Response("Access denied", 401)

if __name__ == '__main__':
   app.run()
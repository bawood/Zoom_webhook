from ast import Str
import json
from flask import Flask, Response, request
import socket
application = Flask(__name__)

@application.route('/hello')
def hello_world():
   return 'Hello World'

@application.route('/emergencycall_alert/', methods = ['POST'])
def zoomphone_alert():
   remote=socket.gethostbyaddr(request.remote_addr)
   token = request.headers.get('authorization', type=str)
   if token:
      print("emergency call alert webhook received from: ", remote[0])
      print("auth token: ", token)
      if request.is_json:
         if request.json:
            print(json.dumps(request.json))
      return Response("", 200)
   else:
      return Response("Access denied", 401)

@application.route('/device_registration/', methods = ['POST'])
def zoomphone_registration():
   remote=socket.gethostbyaddr(request.remote_addr)
   token = request.headers.get('authorization', type=str)
   if token:
      print("device registration webhook received from: ", remote[0])
      print("auth token: ", token)
      if request.is_json:
         if request.json:
            print(json.dumps(request.json))
      return Response("", 200)
   else:
      return Response("Access denied", 401)

if __name__ == '__main__':
   application.host="0.0.0.0"
   application.run()
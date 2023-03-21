from datetime import datetime
from dateutil import tz
from flask import Flask, Response, request
from flask_mysqldb import MySQL
from umichemail import send_mail

import json
import socket
import logging


application = Flask(__name__)

application.config.from_prefixed_env()
mysql = MySQL(application)
mail_from = application.config["MAIL_FROM"]
mail_to = application.config["MAIL_TO"]


def reverseLookup(IP):
    try:
        return socket.gethostbyaddr(IP)[0].lower()
    except Exception:
        return IP


@application.route('/hello')
def hello_world():
#    send_mail(subject='Ignore: Zoom webhook test message',
#              message='received a get request for /hello url from host {}'.format(reverseLookup(request.remote_addr)),
#              from_address=mail_from, to_address=mail_to)
    return 'Hello World'


@application.route('/device_registration/', methods=['POST'])
def zoomphone_registration():
    token = request.headers.get('authorization', type=str)
    if token == application.config["ZOOM_TOKEN"]:
        logging.info("device registration webhook received from: ",
                     reverseLookup(request.remote_addr))
        if request.is_json:
            data = request.get_json()
            if data:
                device_id = data['payload']['object']['device_id']
                mac_address = data['payload']['object']['mac_address']
                logging.info("got webhook for device_id: {} mac_address: {}".format(
                    device_id, mac_address))

                ts = datetime.now(tz=tz.gettz('America/Detroit'))
                sql_vals = (device_id, ts.strftime(
                    '%Y-%m-%d %H:%M:%S'), "ph_" + mac_address + "%")
                sql = "UPDATE ZoomPhoneNameFloorRoom SET deviceId = %s, stamp = %s WHERE PhoneName LIKE %s"
                logging.debug(
                    'Attempting mysql update with: {}'.format(sql_vals))
                try:
                    cur = mysql.connection.cursor()
                    if not cur:
                        msg = 'Unable to connect to MySQL DB: {}:{}'.format(
                            application.config["MYSQL_HOST"], application.config["MYSQL_DB"])
                        logging.error(msg)
                        send_mail(message=msg, subject='ERROR: Zoom webhook Mysql connection',
                                  from_address=mail_from, to_address=mail_to)
                        return Response("Database connection failed", headers='Retry-After: 300', status=503)
                    else:
                        result = cur.execute(sql, sql_vals)
                        mysql.connection.commit()
                        cur.close()
                        if result == 0:
                            msg = 'Manual work is likely required since a webhook was received but no rows in DB were updated for phone with MAC: {}'.format(
                                mac_address)
                            logging.error(msg)
                            send_mail(message=msg, subject='Notice: Zoom webhook, but no DB entry updated',
                                      from_address=mail_from, to_address=mail_to)
                except Exception as e:
                    mysql.connection.rollback()
                    send_mail(message=e, subject='SQL Exception occurred',
                              from_address=mail_from, to_address=mail_to)
                    logging.error("SQL Exception occurred: ", e)
        return Response("", 200)
    else:
        print("invalid auth token: ", token, "from host: ",
              reverseLookup(request.remote_addr))
        return Response("Access denied", 401)


if __name__ == '__main__':
    application.run()

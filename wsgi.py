from datetime import datetime
from random import random
from time import sleep
from dateutil import tz
from flask import Flask, Response, request
from flask_mysqldb import MySQL
from umichemail import send_mail
from dotenv import load_dotenv
from utils import *

import logging
import os


app = Flask(__name__)
application = app

load_dotenv(override=True)
app.config.from_prefixed_env()
mysql = MySQL(app)
mail_from = app.config["MAIL_FROM"]
mail_to = app.config["MAIL_TO"]
log_level = os.environ.get('LOGLEVEL', 'info').upper()
secret = os.environ.get('SECRET', 'none')
logging.basicConfig(level=log_level)


@app.route('/hello')
def hello_world():
    if request.remote_addr.startswith('67.149'):
        app.logger.info("hello request from %s", request.remote_addr)
#    send_mail(subject='Ignore: Zoom webhook test message',
#              message='received a get request for /hello url from host {}'.format(reverseLookup(request.remote_addr)),
#              from_address=mail_from, to_address=mail_to)
    return 'Hello World'


@app.route('/health')
def test_mysql():
    if test_mysql_connection(app, mysql) and test_mysql_query(app, mysql):
        return "MySQL connection and query test successful."
    else:
        return "MySQL connection or query test failed.", 500


@app.route('/device_registration/', methods=['POST'])
def zoomphone_registration():
    if not request.is_json:
        return Response("Invalid request", status=400)

    if not validate_request(app, request, secret):
        print("could not validate request hash from host: ",
              reverseLookup(request.remote_addr))
        return Response("Access denied", 401)
    else:
        app.logger.debug("device registration webhook received from: %s",
                        reverseLookup(request.remote_addr))
        app.logger.debug("x-zm-trackingid: %s", request.headers.get('x-zm-trackingid', 'missing', type=str))
        app.logger.debug("%s", request.data.decode())
        sleep(random())
        if request.is_json:
            data = request.get_json()
            if data:
                device_id = data['payload']['object']['device_id']
                mac_address = data['payload']['object']['mac_address']
                app.logger.info("got webhook for device_id: {} mac_address: {}".format(
                    device_id, mac_address))

                ts = datetime.now(tz=tz.gettz('America/Detroit'))
                sql_vals = (device_id, ts.strftime(
                    '%Y-%m-%d %H:%M:%S'), "ph_" + mac_address + "%")
                sql = "UPDATE ZoomPhoneNameFloorRoom SET deviceId = %s, stamp = %s WHERE PhoneName LIKE %s"
                app.logger.debug(
                    'Attempting mysql update with: {}'.format(sql_vals))
                sleep(random())
                try:
                    cur = mysql.connection.cursor()
                    if not cur:
                        msg = 'Unable to connect to MySQL DB: {}:{}'.format(
                            app.config["MYSQL_HOST"], app.config["MYSQL_DB"])
                        app.logger.error(msg)
                        send_mail(message=msg, subject='ERROR: Zoom webhook Mysql connection',
                                    from_address=mail_from, to_address=mail_to)
                        return Response("Database connection failed", headers='Retry-After: 300', status=503)
                    else:
                        result = cur.execute(sql, sql_vals)
                        mysql.connection.commit()
                        if result == 0:
                            sql = "INSERT INTO ZoomPhoneNameFloorRoom ( PhoneName, deviceId, stamp ) VALUES(%s, %s, %s);"
                            sql_vals = ("ph_" + mac_address, device_id, ts.strftime('%Y-%m-%d %H:%M:%S'))
                            result = cur.execute(sql, sql_vals)
                            mysql.connection.commit()
                            app.logger.debug("SQL insert result: %s", result)
                            msg = 'device registration webhook was received but no existing entries in DB matched for phone with MAC: {}'.format(
                                mac_address)
                            app.logger.error(msg)
                            send_mail(message=msg, subject='Notice: Zoom device registration, missing DB entry',
                                        from_address=mail_from, to_address=mail_to)
                    cur.close()
                except MySQL.IntegrityError as e:
                    mysql.connection.rollback()
                    cur.close()
                    app.logger.error("IntegrityError: %s", e)
                except Exception as e:
                    mysql.connection.rollback()
                    cur.close()
                    send_mail(message=str(e), subject='SQL Exception occurred',
                                from_address=mail_from, to_address=mail_to)
                    app.logger.error("SQL Exception occurred: ", str(e))
        return Response("", 200)


if __name__ == '__main__':
    app.run()

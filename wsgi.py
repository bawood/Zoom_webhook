from datetime import datetime
from dateutil import tz
from flask import Flask, Response, request
from flask_mysqldb import MySQL
from umichemail import send_mail
from dotenv import load_dotenv

import json
import socket
import logging


app = Flask(__name__)
application = app

load_dotenv(override=True)
app.config.from_prefixed_env()
mysql = MySQL(app)
mail_from = app.config["MAIL_FROM"]
mail_to = app.config["MAIL_TO"]
logging.basicConfig(level=logging.INFO)


def reverseLookup(IP):
    try:
        return socket.gethostbyaddr(IP)[0].lower()
    except Exception:
        return IP


def test_mysql_connection():
    try:
        conn = mysql.connection.cursor()
        if conn:
            app.logger.debug("Mysql test connection successful")
            return True
        else:
            app.logger.error("Mysql test connection failed")
            return False
    except Exception as e:
        app.logger.error("Mysql connection test exception {}".format(e))
        return False


def test_mysql_query():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchall()
        if result:
            app.logger.debug("Mysql %s test query successful", result)
            return True
        else:
            app.logger.error("Mysql test query failed")
            return False
    except Exception as e:
        app.logger.error("Mysql query test exception %s", e.__cause__)
        return False


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
    if test_mysql_connection() and test_mysql_query():
        return "MySQL connection and query test successful."
    else:
        return "MySQL connection or query test failed.", 500


@app.route('/device_registration/', methods=['POST'])
def zoomphone_registration():
    token = request.headers.get('authorization', type=str)
    if token == app.config["ZOOM_TOKEN"]:
        app.logger.debug("device registration webhook received from: %s",
                     reverseLookup(request.remote_addr))
        app.logger.debug("%s", request.data)
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
                            sql = "INSERT INTO ZoomPhoneNameFloorRoom ( deviceId, stamp ) VALUES(%s, %s);"
                            sql_vals = (device_id, ts.strftime('%Y-%m-%d %H:%M:%S'))
                            result = cur.execute(sql, sql_vals)
                            mysql.connection.commit()
                            app.logger.debug("SQL insert result: %s", result)
                            msg = 'device registration webhook was received but no existing entries in DB matched for phone with MAC: {}'.format(
                                mac_address)
                            app.logger.error(msg)
                            send_mail(message=msg, subject='Notice: Zoom device registration, missing DB entry',
                                      from_address=mail_from, to_address=mail_to)
                    cur.close()
                except Exception as e:
                    mysql.connection.rollback()
                    cur.close()
                    send_mail(message=e, subject='SQL Exception occurred',
                              from_address=mail_from, to_address=mail_to)
                    app.logger.error("SQL Exception occurred: ", e)
        return Response("", 200)
    else:
        print("invalid auth token: ", token, "from host: ",
              reverseLookup(request.remote_addr))
        return Response("Access denied", 401)


if __name__ == '__main__':
    app.run()

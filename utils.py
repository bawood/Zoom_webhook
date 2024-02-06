import hashlib
import hmac
import socket



def reverseLookup(IP):
    try:
        return socket.gethostbyaddr(IP)[0].lower()
    except Exception:
        return IP


def test_mysql_connection(app, mysql):
    try:
        conn = mysql.connection.cursor()
        if conn:
            #app.logger.debug("Mysql test connection successful")
            return True
        else:
            app.logger.error("Mysql test connection failed")
            return False
    except Exception as e:
        app.logger.error("Mysql connection test exception {}".format(e))
        return False


def test_mysql_query(app, mysql):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchall()
        if result:
            #app.logger.debug("Mysql %s test query successful", result)
            return True
        else:
            app.logger.error("Mysql test query failed")
            return False
    except Exception as e:
        app.logger.error("Mysql query test exception %s", e.__cause__)
        return False


def validate_request(app, request, secret):
    zm_request_timestamp = request.headers.get('x-zm-request-timestamp')
    message = f'v0:{zm_request_timestamp}:{request.data.decode("utf-8")}'
    our_sig = 'v0=' + hmac.new(secret.encode("utf-8"),
                               message.encode("utf-8"),
                               hashlib.sha256 ).hexdigest()
    app.logger.debug("our signature: %s", our_sig)
    zm_signature = request.headers.get('x-zm-signature', type=str)
    app.logger.debug("x-zm-signature: %s", zm_signature)
    return zm_signature == our_sig
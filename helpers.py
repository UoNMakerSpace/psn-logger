from datetime import datetime
import smtplib
import ssl

import pymysql

import config


def db_connection():
    return pymysql.connect(
        config.database_address, config.database_username,
        config.database_password, config.database_name)

def get_active_session(node_address):
    """ Gets the active session for a sensor node.
    """
    QUERY = ("SELECT session_id, `interval`, batch_size FROM session_nodes WHERE "
        "node_id = (SELECT node_id FROM nodes WHERE mac_address = %s) AND "
        "NOW() >= start_time AND (end_time = NULL OR NOW() < end_time)")
    connection = None

    try:
        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(QUERY, (node_address))
        result = cursor.fetchone()

        connection.close()
        return result

    except:
        if connection != None: connection.close()
        raise

def is_time_in_session(node_address, session_id, time):
    """ Checks whether a time is within the start and end time of a sensor node
        inside a session.
    """
    QUERY = ("SELECT 0 FROM session_nodes WHERE session_id = %s AND "
        "node_id = (SELECT node_id FROM nodes WHERE mac_address = %s) AND "
        "%s >= start_time AND (end_time = NULL OR %s <= end_time)")
    connection = None

    try:
        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(QUERY, (session_id, node_address, time, time))
        result = cursor.fetchone()

        connection.close()
        return False if result == None else True

    except:
        if connection != None: connection.close()
        raise

def insert_report(node_address, report):
    """ Inserts a report from a node into the database.
    """
    QUERY = ("INSERT INTO reports (session_id, node_id, time, airt, relh, batv) "
        "VALUES (%s, (SELECT node_id FROM nodes WHERE mac_address = %s), %s, %s, %s, %s)")
    connection = None

    try:
        report_time = datetime.strptime(report["time"], "%Y-%m-%dT%H:%M:%SZ")
        values = (report["session_id"], node_address,
            report_time.strftime("%Y-%m-%d %H:%M:%S"), report["airt"], report["relh"],
            report["batv"])

        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(QUERY, values)
        connection.commit()
        connection.close()

    except:
        if connection != None: connection.close()
        raise

def get_triggered_alarms(node_address, session_id, parameter, value):
    """ Gets any alarms that are triggered according to the alarm valid range
    """
    QUERY = ("SELECT alarm_id, (SELECT name FROM sessions WHERE session_id = %s) AS session_name, "
        "(SELECT location FROM session_nodes WHERE session_id = %s AND node_id = (SELECT node_id FROM nodes WHERE mac_address = %s)) AS node_location, "
        "parameter, minimum, maximum, (SELECT user_id FROM sessions WHERE session_id = %s), %s "
        "FROM session_alarms WHERE session_id = %s "
        "AND node_id = (SELECT node_id FROM nodes WHERE mac_address = %s) "
        "AND parameter = %s AND (%s NOT BETWEEN minimum AND maximum) "
        "AND (last_triggered IS NULL OR last_triggered <= DATE_SUB(NOW(), INTERVAL %s MINUTE))")
    connection = None

    try:
        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(QUERY, (session_id, session_id, node_address, session_id, value, session_id,
            node_address, parameter, value, config.min_trigger_interval))
        result = cursor.fetchall()

        connection.close()
        if len(result) == 0: return None
        return result

    except:
        if connection != None: connection.close()
        raise

def update_alarm_triggered(alarm_id, report_time):
    """ Updates the last triggered time of the specified alarm.
    """
    QUERY = ("UPDATE session_alarms SET last_triggered = %s WHERE alarm_id = %s")
    connection = None

    try:
        connection = db_connection()
        cursor = connection.cursor()

        cursor.execute(QUERY, (report_time.strftime("%Y-%m-%d %H:%M:%S"), alarm_id))
        connection.commit()
        connection.close()

    except:
        if connection != None: connection.close()
        raise

def trigger_alarms(alarms, report_time):
    """ Sends an email to the owner of a session to indicate a triggered alarm
    """
    if alarms == None: return

    message = (
        "Subject: PSN Alarm Triggered\n\n"
        "This is a notice from the Phenotyping Sensor Network that a sensor node in one "
        "of your sessions raised an alarm on {0} UTC."
        "\n\nSession Name: {1}"
        "\nNode Location: {2}"
        "\nAlarm: {3} (Safe Value Range: {4} - {5})"
        "\nCurrent Value (on {6} UTC): {7}")
    
    for alarm in alarms:
        parameter_friendly = ""
        if alarm[3] == "airt": parameter_friendly = "Temperature"
        elif alarm[3] == "relh": parameter_friendly = "Humidity"
        if alarm[3] == "batv": parameter_friendly = "Battery Voltage"

        # Email the owner of the session
        server = smtplib.SMTP_SSL(config.email_server, 465)
        server.login(config.email_address, config.email_password)

        time_string = report_time.strftime("%d/%m/%Y at %H:%M")
        message_formatted = message.format(time_string, alarm[1], alarm[2], parameter_friendly,
            alarm[4], alarm[5], time_string, alarm[7])
        server.sendmail(config.email_address, alarm[6], message_formatted)
        server.quit()

        # Prevent alarm from triggering again within certain time period
        update_alarm_triggered(alarm[0], report_time)

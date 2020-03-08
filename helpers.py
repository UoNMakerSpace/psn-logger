from datetime import datetime

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
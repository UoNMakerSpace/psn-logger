import pymysql

import config

def db_connection():
    return pymysql.connect(config.database_address, config.database_username,
        config.database_password, config.database)

def get_active_session(node_address):
    connection = db_connection()

    try:
        QUERY = ("SELECT sessions.session_id, sessions.interval, "
            + "sessions.batch_size FROM sessions NATURAL JOIN session_nodes "
            + "WHERE session_nodes.node_id = (SELECT node_id FROM nodes WHERE "
            + "mac_address = %s) AND (sessions.end_time = NULL OR NOW() <= "
            + "sessions.end_time)")

        cursor = connection.cursor()
        cursor.execute(QUERY, (node_address))
        result = cursor.fetchone()
        connection.close()

        return False if result == None else result

    except:
        connection.close()
        raise

def is_session_active(session_id, time):
    connection = db_connection()

    try:
        QUERY = ("SELECT 1 FROM sessions WHERE session_id = %s AND (sessions"
            + ".end_time = NULL OR %s <= sessions.end_time)")

        cursor = connection.cursor()
        cursor.execute(QUERY, (session_id, time))
        result = cursor.fetchone()
        connection.close()

        return False if result == None else True

    except:
        connection.close()
        raise

def insert_report(node_address, time, report):
    connection = db_connection()

    try:
        QUERY = ("INSERT INTO reports (session_id, node_id, time, airt, relh, "
            + "lght, batv) VALUES (%s, (SELECT node_id FROM nodes WHERE "
            + "mac_address = %s), %s, %s, %s, %s, %s)")
        data_tuple = (report["session"], node_address, time, report["airt"],
            report["relh"], report["lght"], report["batv"])

        cursor = connection.cursor()
        cursor.execute(QUERY, data_tuple)
        connection.commit()
        connection.close()

    except:
        connection.close()
        raise

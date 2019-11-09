import pymysql

import config

def db_connection():
    return pymysql.connect(config.database_address, config.database_username,
        config.database_password, config.database)

def get_active_session(node_id):
    connection = db_connection()

    try:
        QUERY = ("SELECT sessions.session_id, sessions.interval, "
            + "sessions.batch_size FROM sessions NATURAL JOIN session_nodes "
            + "WHERE session_nodes.node_id = %s AND (sessions.end_time = NULL "
            + "OR NOW() <= sessions.end_time)")

        cursor = connection.cursor()
        cursor.execute(QUERY, (node_id))
        result = cursor.fetchone()
        connection.close()

        return False if result == None else result

    except:
        connection.close()
        raise

def is_session_active(node_id, session_id, time):
    connection = db_connection()

    try:
        QUERY = ("SELECT 1 FROM sessions NATURAL JOIN session_nodes WHERE "
            + "session_nodes.node_id = %s AND sessions.session_id = %s AND "
            + "(sessions.end_time = NULL OR %s <= sessions.end_time)")

        cursor = connection.cursor()
        cursor.execute(QUERY, (node_id, session_id, time))
        result = cursor.fetchone()
        connection.close()

        return False if result == None else True

    except:
        connection.close()
        raise

def insert_report(node_id, time, report):
    connection = db_connection()

    try:
        QUERY = "INSERT INTO reports VALUES (%s, %s, %s, %s, %s, %s, %s)"
        data_tuple = (node_id, time, report["airt"], report["relh"],
            report["lvis"], report["lifr"], report["batv"])

        cursor = connection.cursor()
        cursor.execute(QUERY, data_tuple)
        connection.commit()
        connection.close()

    except:
        connection.close()
        raise

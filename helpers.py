import pymysql

def log(message):
    print("LOG: " + message)

def db_connection():
    return pymysql.connect("localhost", "root2", "password", "psn")

def node_exists(node_id):
    connection = db_connection()

    try:
        QUERY = "SELECT 1 FROM nodes WHERE node_id = %s"

        cursor = connection.cursor()
        cursor.execute(QUERY, (node_id))
        result = cursor.fetchone()
        connection.close()

        return False if result == None else True

    except:
        connection.close()
        raise

def insert_report(data):
    connection = db_connection()

    try:
        QUERY = "INSERT INTO reports VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        data_tuple = (data["node"], data["time"], data["airt"], data["relh"],
            data["lvis"], data["lifr"], data["batv"], data["sigs"])

        cursor = connection.cursor()
        cursor.execute(QUERY, data_tuple)
        connection.commit()
        connection.close()

    except:
        connection.close()
        raise
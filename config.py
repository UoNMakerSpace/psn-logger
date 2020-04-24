""" Taken from https://github.com/henryshunt/c-aws and modified to support the
    configuration options for this project
"""

from configparser import ConfigParser
from enum import Enum


__parser = ConfigParser()

# Broker group
broker_address = None
broker_port = None

# Database group
database_address = None
database_username = None
database_password = None
database_name = None

# Alarms group
email_server = None
email_address = None
email_password = None
min_trigger_interval = None


def __load_value(group, key, data_type, none_ok):
    """ Returns the value of the specified key, in the specified type
    """
    global __parser

    value = __parser.get(group, key)
    if value == "" and none_ok == True:
        return None
    elif value == "" and none_ok == False:
        raise Exception("None value cannot be None")

    if data_type == __DataType.STRING:
        return __parser.get(group, key)
    elif data_type == __DataType.BOOLEAN:
        return __parser.getboolean(group, key)
    elif data_type == __DataType.INTEGER:
        return __parser.getint(group, key)
    elif data_type == __DataType.FLOAT:
        return __parser.getfloat(group, key)

def load():
    """ Loads data from the config.ini file in the project root directory
    """
    global __parser, broker_address, broker_port, database_address
    global database_username, database_password, database_name, email_server
    global email_address, email_password, min_trigger_interval

    try:
        __parser.read("config.ini")

        # Broker group
        broker_address = __load_value("broker", "address", __DataType.STRING,
            False)
        broker_port = __load_value("broker", "port", __DataType.INTEGER, False)

        # Database group
        database_address = __load_value("database", "address",
            __DataType.STRING, False)
        database_username = __load_value("database", "username",
            __DataType.STRING, False)
        database_password = __load_value("database", "password",
            __DataType.STRING, False)
        database_name = __load_value("database", "database", __DataType.STRING,
            False)

        # Alarms group
        email_server = __load_value("alarms", "email_server", __DataType.STRING,
            False)
        email_address = __load_value("alarms", "email_address",
            __DataType.STRING, False)
        email_password = __load_value("alarms", "email_password",
            __DataType.STRING, False)
        min_trigger_interval = __load_value("alarms", "min_trigger_interval",
            __DataType.INTEGER, False)
    except: return False

    return True


class __DataType(Enum):
    BOOLEAN = 1
    FLOAT = 2
    STRING = 3
    INTEGER = 4
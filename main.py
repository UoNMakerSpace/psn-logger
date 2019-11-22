import json
import os
from datetime import datetime
import sys

import daemon
import paho.mqtt.client as mqtt
import pymysql

import config
import helpers


broker = None

def on_log(client, user_data, level, buffer):
    print(buffer)

def on_connect(client, user_data, flags, result):
    """ Called when the client has connected to the MQTT broker
    """
    if result != 0: return

    while True:
        result = broker.subscribe([("nodes/+/outbound/+", 1),
            ("nodes/+/reports/+", 1)])
        if result[0] == mqtt.MQTT_ERR_SUCCESS: break

def on_message(client, user_data, message):
    """ Called whenever a message is received from the MQTT broker
    """
    topic_sections = message.topic.split('/')
    node_address = topic_sections[1]
    scope = topic_sections[2]
    message_id = topic_sections[3]
    message_data = message.payload.decode()

    if scope == "outbound":
        if message_data == "get_session":
            session = helpers.get_active_session(node_address)
            inbound_topic = "nodes/" + node_address + "/inbound/" + message_id

            if session != False:
                response = ("{ \"session\": " + str(session[0])
                    + ", \"interval\": " + str(session[1])
                    + ", \"batch_size\": " + str(session[2]) + " }")
                broker.publish(inbound_topic, response, 1)
            else: broker.publish(inbound_topic, "no_session", 1)

    elif scope == "reports":
        time = datetime.fromtimestamp(float(message_id))
        report = json.loads(message_data)
        inbound_topic = "nodes/" + node_address + "/inbound/" + message_id

        if helpers.is_session_active(report["session"], time) == True:

            # Ignore duplicate entry exception
            try:
                helpers.insert_report(node_address, time, report)

                # Trigger any matching alarms
                # ...
            except pymysql.IntegrityError as e:
                if e.args[0] != 1062: raise

            broker.publish(inbound_topic, "ok", 1)
        else: broker.publish(inbound_topic, "no_session", 1)


if __name__ == "__main__":
    # current_dir = os.path.dirname(os.path.realpath(__file__))

    # with daemon.DaemonContext(working_directory=current_dir):
    if config.load() == False: sys.exit(1)

    # Check the database is available (loop until success)
    while True:
        try:
            helpers.db_connection()
            break
        except: pass

    # Create and connect to the MQTT broker (loop until success)
    broker = mqtt.Client()
    broker.on_connect = on_connect
    broker.on_message = on_message
    broker.on_log = on_log

    while True:
        try:
            broker.connect(config.broker_address, config.broker_port)
            break
        except: pass

    # Enter loop to handle messages (handles reconnecting)
    try:
        broker.loop_forever()
    except KeyboardInterrupt:
        broker.disconnect()
        exit(0)
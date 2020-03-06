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


def on_connect(client, user_data, flags, result):
    """ Called when the client has connected to the MQTT broker
    """
    if result: return

    # Subscribe to the outbound and reports topics
    while True:
        subscribe_result = broker.subscribe(
            [("nodes/+/outbound/+", 0), ("nodes/+/reports/+", 0)])
        if subscribe_result[0] == mqtt.MQTT_ERR_SUCCESS: break

def on_message(client, user_data, message):
    """ Called whenever a message is received from the MQTT broker
    """
    topic_sections = message.topic.split('/')
    node_address = topic_sections[1]
    scope = topic_sections[2]
    message_id = topic_sections[3]
    message_data = message.payload.decode()

    inbound_topic = "nodes/" + node_address + "/inbound/" + message_id


    if scope == "outbound":
        if message_data == "get_session":
            try:
                session = helpers.get_active_session(node_address)
                if session == None:
                    broker.publish(inbound_topic, "no_session", 0)
                    return

                response = ("{{ \"session_id\": {0}, \"interval\": {1}, \"batch_size\": {2} }}"
                    .format(str(session[0]), str(session[1]), str(session[2])))
                broker.publish(inbound_topic, response, 0)
            except: broker.publish(inbound_topic, "error", 0)

    elif scope == "reports":
        try:
            report = json.loads(message_data)
            report_time = datetime.strptime(report["time"], "%Y-%m-%dT%H:%M:%SZ")
        
            if helpers.is_time_in_session(node_address, report["session_id"], report_time):
                try:
                    helpers.insert_report(node_address, report)

                    # Trigger any matching alarms
                    # ...
                except pymysql.IntegrityError as e:

                    # Report for this node with this time already exists (unique key
                    # constraint fails)
                    if e.args[0] == 1062: pass
                    
                    # Session and/or node does not exist (foreign key constraint fails)
                    elif e.args[0] == 1452:
                        broker.publish(inbound_topic, "no_session", 0)
                        return
                    else: raise

                broker.publish(inbound_topic, "ok", 0)
            else: broker.publish(inbound_topic, "no_session", 0)
        except: broker.publish(inbound_topic, "error", 0)


if __name__ == "__main__":
    # current_dir = os.path.dirname(os.path.realpath(__file__))

    # with daemon.DaemonContext(working_directory=current_dir):
    if not config.load(): sys.exit(1)

    # Check if the database is available
    try:
        helpers.db_connection()
    except: sys.exit(1)

    # Create and connect to the MQTT broker (loop until success)
    broker = mqtt.Client()
    broker.on_connect = on_connect
    broker.on_message = on_message
    broker.on_log = lambda client, user_data, level, buffer: print(buffer)

    while True:
        try:
            broker.connect(config.broker_address, config.broker_port)
            break
        except: pass

    # Enter loop to handle messages (handles auto-reconnecting)
    try:
        broker.loop_forever()
    except KeyboardInterrupt:
        broker.disconnect()
        exit(0)
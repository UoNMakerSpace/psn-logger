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
    if result: return # Return if error

    # Subscribe to the outbound and reports topics
    subscribe_result = broker.subscribe(
        [("nodes/+/outbound/+", 1), ("nodes/+/reports/+", 1)])

def on_message(client, user_data, message):
    topic_sections = message.topic.split('/')
    node_address = topic_sections[1]
    endpoint = topic_sections[2]
    message_id = topic_sections[3]

    inbound_topic = "nodes/" + node_address + "/inbound/" + message_id

    # Request received from a sensor node
    if endpoint == "outbound":

        # Send back the active session for this sensor node
        if message.payload.decode() == "get_session":
            try:
                session = helpers.get_active_session(node_address)
                if session == None:
                    broker.publish(inbound_topic, "no_session", 0)
                    return

                response = ("{{\"session_id\":{0},\"interval\":{1},\"batch_size\":{2}}}"
                    .format(str(session[0]), str(session[1]), str(session[2])))
                broker.publish(inbound_topic, response, 0)
            except: broker.publish(inbound_topic, "error", 0)

    # Report received from a sensor node
    elif endpoint == "reports":
        try:
            report = json.loads(message.payload.decode())
            report_time = datetime.strptime(report["time"], "%Y-%m-%dT%H:%M:%SZ")
        
            # Add to database if report time is within time range of specified session
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
    current_dir = os.path.dirname(os.path.realpath(__file__))

    with daemon.DaemonContext(working_directory=current_dir):
        if not config.load(): sys.exit(1)

        # Check if the database is accessible
        try:
            helpers.db_connection()
        except: sys.exit(1)

        # Create and connect to the MQTT broker
        broker = mqtt.Client()
        broker.on_connect = on_connect
        broker.on_message = on_message

        try:
            broker.connect(config.broker_address, config.broker_port)
        except: sys.exit(1)

        # Enter loop to receive messages (handles auto-reconnecting)
        broker.loop_forever()
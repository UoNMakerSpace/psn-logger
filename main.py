import json

import paho.mqtt.client as mqtt
import pymysql

import helpers


mqtt_client = None

def on_connect(client, user_data, flags, result):
    """ Called when the client has connected to the MQTT broker
    """
    if result != 0: return

    mqtt_client.subscribe("nodes/#")

def on_message(client, user_data, message):
    """ Called whenever a message is received from the MQTT broker
    """
    if not message.topic.startswith("nodes/"): return

    # Parse the message JSON
    try:
        data = json.loads(message.payload.decode())
    except: helpers.log("on_message 0")

    # Save the report if it came from a registered node
    try:
        if helpers.node_exists(data["node"]) == True:
            try:
                helpers.insert_report(data)
            except: helpers.log("on_message 2")
    except: helpers.log("on_message 1")


if __name__ == "__main__":
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Connect to the MQTT broker
    while True:
        try:
            mqtt_client.connect("localhost", 1883)

            # Automatically handles reconnection
            mqtt_client.loop_forever()
        except: helpers.log("__main__ 0")

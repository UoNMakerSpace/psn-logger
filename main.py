import json
import os
from datetime import datetime
import sys
import queue
import threading
import smtplib
import ssl

import daemon
import paho.mqtt.client as mqtt
import pymysql

import config
import helpers


broker = None
alarm_analysis_queue = queue.Queue()
is_processing_alarms = False


def on_connect(client, user_data, flags, result):
    """ Called when the MQTT broker connects to an MQTT server
    """
    if result: return # Return if error

    # Subscribe to the outbound and reports topics
    subscribe_result = broker.subscribe(
        [("nodes/+/outbound/+", 1), ("nodes/+/reports/+", 1)])


def send_alarm_email(alarm, report_time, value):
    """ Sends an email to the owner of a session to indicate a triggered alarm
    """
    message = (
        "Subject: PSN Alarm Triggered\n\n"
        "Notice from the Phenotyping Sensor Network that a sensor node in one of your "
        "sessions raised an alarm."
        "\n\nAlarm triggered based on data on {0} UTC"
        "\n\nSession name: {1}"
        "\nSensor node location: {2}"
        "\nAlarm: {3} (safe value range: {4} - {5})"
        "\nReported value: {6}")
    
    parameter_friendly = ""
    if alarm[1] == "airt": parameter_friendly = "Temperature"
    elif alarm[1] == "relh": parameter_friendly = "Humidity"
    if alarm[1] == "batv": parameter_friendly = "Battery Voltage"

    # Email the owner of the session
    server = smtplib.SMTP_SSL(config.email_server, 465)

    try:
        server.login(config.email_address, config.email_password)

        time_string = report_time.strftime("%d/%m/%Y at %H:%M")
        message_formatted = message.format(time_string, alarm[4], alarm[5],
            parameter_friendly, alarm[2], alarm[3], value)
        server.sendmail(config.email_address, alarm[6], message_formatted)
    except: pass

    server.quit()

def process_alarms():
    """ Checks all reports in the alarm analysis queue to see if they trigger any alarms
        and triggers the alarms if they do
    """
    global is_processing_alarms
    if is_processing_alarms == True: return
    is_processing_alarms = True

    while alarm_analysis_queue.empty() == False:
        report = alarm_analysis_queue.get()
        report_time = datetime.strptime(report[1]["time"], "%Y-%m-%dT%H:%M:%SZ")

        try:
            # Get all alarms for this node that may be able to trigger
            alarms = helpers.get_triggered_alarms(report[0], report[1]["session_id"],
                report_time)
            if alarms == None: continue

            # Trigger any alarms that have a report value outside the alarm range
            for alarm in alarms:
                try:
                    if alarm[1] == "airt":
                        if (report[1]["airt"] != None and
                            (report[1]["airt"] < alarm[2] or report[1]["airt"] > alarm[3])):
                            helpers.update_alarm_triggered(alarm[0], report_time)
                            send_alarm_email(alarm, report_time, report[1]["airt"])

                    elif alarm[1] == "relh":
                        if (report[1]["relh"] != None and
                            (report[1]["relh"] < alarm[2] or report[1]["relh"] > alarm[3])):
                            helpers.update_alarm_triggered(alarm[0], report_time)
                            send_alarm_email(alarm, report_time, report[1]["relh"])

                    elif alarm[1] == "batv":
                        if (report[1]["batv"] != None and
                            (report[1]["batv"] < alarm[2] or report[1]["batv"] > alarm[3])):
                            helpers.update_alarm_triggered(alarm[0], report_time)
                            send_alarm_email(alarm, report_time, report[1]["batv"])
                except: continue
        except: continue

    is_processing_alarms = False

def on_message(client, user_data, message):
    """ Called when a message is received from the MQTT broker
    """
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

                    # Trigger any alarms based on the values in this report
                    alarm_analysis_queue.put((node_address, report))
                    threading.Thread(target=process_alarms).start()
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
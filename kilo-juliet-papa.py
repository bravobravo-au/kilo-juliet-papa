#!./bin/python3
"""
Kilo Juliet Papa

A bridge between all that is MQTT and Raspberry Pi GPIO. Allowing non coders to control the real world using MQTT.

https://github.com/bravobravo-au

"""
import paho.mqtt.client as mqtt
from time import strftime, gmtime, sleep
import configparser
import argparse
import RPi.GPIO as GPIO
import json

"""
Parser of MQTT messages in JSON taking an Integer and returning a BOOL

ARG1 is used to specify the name to use to trigger off

0 is logic Low and anything else is logic High
"""
def PARSER_JSONINT(message, config):
    jsonDecode = json.loads( str(message.payload.decode("utf-8")) )

    if args.debug == True:
        print("%s -- %s" % (message.topic,jsonDecode))

        value = int(jsonDecode[config['MQTT_PARSER_ARG1']])
        if value == 0:
            value = GPIO.LOW
        else:
            value = GPIO.HIGH
    return value


"""
Parser of MQTT messages in JSON taking a String and returning a BOOL

ARG1 is used to specify the name to use to trigger off

OFF is logic Low and ON is logic High
"""
def PARSER_STRONOFF(message, config):
    messagePayload = message.payload.decode("utf-8")
    if args.debug == True:
        print("%s -- %s" % (message.topic,messagePayload))
    if messagePayload == 'OFF':
        value = GPIO.LOW
    if messagePayload == 'ON':
        value = GPIO.HIGH
    return value


def mqtt_message(client, userdata, message):
    global GPIO

    for gpioConfig in gpioConfigs:
        if message.topic == gpioConfig['MQTT_TOPIC'] and gpioConfig['GPIO_TYPE'] == 'OUTPUT':
            functionName = "PARSER_" + gpioConfig['MQTT_PARSER']
            value = globals()[ functionName ]( message, gpioConfig )
            GPIO.output( 
                            int(gpioConfig['GPIO_PIN']), 
                            value
                            )

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

gpioConfigs = []

parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Configuration file to use default config.ini")
parser.add_argument("--debug", help="print debugging to console")
args = parser.parse_args()

if args.debug:
    print("Console debug turned on")
    args.debug = True
else:
    args.debug = False

config = configparser.ConfigParser()
if args.config:
    config.read(args.config)
else:
    config.read('config.ini')

mqtt_host                           = config['DEFAULT']['MQTT_HOST']
mqtt_port                           = config['DEFAULT']['MQTT_PORT']
mqtt_client_name                    = config['DEFAULT']['MQTT_CLIENT_NAME']
if 'MQTT_USERNAME' in config['DEFAULT']:
    mqtt_username                   = config['DEFAULT']['MQTT_USERNAME'] 
    mqtt_password                   = config['DEFAULT']['MQTT_PASSWORD']
else:
    mqtt_username                   = None
    mqtt_password                   = None


client = mqtt.Client(
                        client_id=mqtt_client_name, 
                        clean_session=False, 
                        userdata=None, 
                        transport='tcp'
                        )
if mqtt_username is not None:
    client.username_pw_set(username=mqtt_username, password=mqtt_password)

client.connect(
                        mqtt_host, 
                        port=int(mqtt_port), 
                        keepalive=10, 
                        bind_address=""
                        )
client.on_message=mqtt_message


"""
Loop through each addition config section and create an input or output
"""
for section in config.sections():
    gpioConfigs.append( {
                            'MQTT_TOPIC':       config[section]['MQTT_TOPIC'],
                            'GPIO_PIN':         config[section]['GPIO_PIN'],
                            'GPIO_TYPE':        config[section]['GPIO_TYPE'],
                            'MQTT_PARSER':      config[section]['MQTT_PARSER'],
                            'MQTT_PARSER_ARG1': config[section]['MQTT_PARSER_ARG1'],
                            } )
    if config[section]['GPIO_TYPE'] == 'OUTPUT':
        GPIO.setup( 
                    int(config[section]['GPIO_PIN']), 
                    GPIO.OUT
                    )
    client.subscribe( 
                        config[section]['MQTT_TOPIC'],
                        )

client.loop_forever(
                        timeout=1.0, 
                        max_packets=1, 
                        retry_first_connection=False
                        )


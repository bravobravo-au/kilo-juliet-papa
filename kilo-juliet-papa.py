#!./bin/python3
"""
Copyright (c) 2019, bravobravo-au
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, this
       list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the documentation
        and/or other materials provided with the distribution.

    3. Neither the name of the copyright holder nor the names of its
        contributors may be used to endorse or promote products derived from
        this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import paho.mqtt.client as mqtt
from time import strftime, gmtime, sleep
import configparser
import argparse
import RPi.GPIO as GPIO
import json
import logging

"""
Parser of MQTT messages in JSON taking an Integer and returning a BOOL

ARG1 is used to specify the name to use to trigger off

0 is logic Low and anything else is logic High
"""
def PARSER_JSONINT(message, config):
    jsonDecode = json.loads( str(message.payload.decode("utf-8")) )

    logger.debug("JSONINT Topic: %s Payload: %s" % (message.topic,jsonDecode))

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
    
    logger.debug("STRONOFF Topic: %s Payload: %s" % (message.topic,messagePayload))

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
            logger.info(gpioConfig['LOG_MESSAGE'] % { 'pin': gpioConfig['GPIO_PIN'], 'value': value, 'message': message.payload.decode("utf-8"), 'topic': message.topic })

        if message.topic == gpioConfig['TOGGLE_MQTT_TOPIC'] and gpioConfig['GPIO_TYPE'] == 'OUTPUT':
            value = not GPIO.input( gpioConfig['GPIO_PIN'] )
            GPIO.output(
                            int(gpioConfig['GPIO_PIN']),
                            value
                            )
            client.publish(
                            topic= gpioConfig['MQTT_TOPIC'], 
                            payload=gpioConfig['TOGGLE_MQTT_MESSAGE'].replace('{VALUE}',str(int(value)*100) ),
                            qos=gpioConfig['MQTT_QOS'],
                            retain=gpioConfig['MQTT_RETAIN'],
                            )

            logger.info(gpioConfig['LOG_MESSAGE'] % { 'pin': gpioConfig['GPIO_PIN'], 'value': value, 'message': message.payload.decode("utf-8"), 'topic': message.topic })

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

gpioConfigs = []

parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Configuration file to use default config.ini")
parser.add_argument("--debug", help="print debugging to console")
args = parser.parse_args()

config = configparser.ConfigParser(interpolation=None)
if args.config:
    config.read(args.config)
else:
    config.read('config.ini')

mqtt_host                           = config['DEFAULT']['MQTT_HOST']
mqtt_port                           = int(config['DEFAULT']['MQTT_PORT'])
mqtt_client_name                    = config['DEFAULT']['MQTT_CLIENT_NAME']
mqtt_loop_delay                     = float(config['DEFAULT']['MQTT_LOOP_DELAY'])

if 'MQTT_USERNAME' in config['DEFAULT']:
    mqtt_username                   = config['DEFAULT']['MQTT_USERNAME'] 
    mqtt_password                   = config['DEFAULT']['MQTT_PASSWORD']
else:
    mqtt_username                   = None
    mqtt_password                   = None

if 'LOGFILE_NAME' in config['DEFAULT']:
    logfile_name                    = config['DEFAULT']['LOGFILE_NAME']
else:
    logfile_name                    = None

if args.debug:
    logging.basicConfig(filename=logfile_name, format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(filename=logfile_name, format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

client = mqtt.Client(   client_id=mqtt_client_name, 
                        clean_session=False, 
                        userdata=None, 
                        transport='tcp',
                        )
if mqtt_username is not None:
    client.username_pw_set(username=mqtt_username, password=mqtt_password)

client.connect(         mqtt_host, 
                        port=mqtt_port, 
                        keepalive=10, 
                        )
client.on_message=mqtt_message


"""
Loop through each addition config file section and create an input or output
"""
for section in config.sections():
    mqtt_topic                  = config[section]['MQTT_TOPIC']
    gpio_pin                    = int(config[section]['GPIO_PIN'])
    gpio_type                   = config[section]['GPIO_TYPE']
    mqtt_parser                 = None
    mqtt_parser_arg1            = None
    mqtt_message                = None
    gpio_pin_state              = None
    mqtt_message_processor      = None
    mqtt_retain                 = bool(config[section]['MQTT_RETAIN'])
    mqtt_qos                    = int(config[section]['MQTT_QOS'])
    log_message                 = config[section]['LOG_MESSAGE']

    if gpio_type == 'OUTPUT':
        mqtt_parser             = config[section]['MQTT_PARSER']
        mqtt_parser_arg1        = config[section]['MQTT_PARSER_ARG1']
        toggle_mqtt_topic       = config[section]['TOGGLE_MQTT_TOPIC']
        toggle_mqtt_message     = config[section]['TOGGLE_MQTT_MESSAGE']

        GPIO.setup( 
                    gpio_pin, 
                    GPIO.OUT,
                    )
        client.subscribe( 
                        mqtt_topic,
                        )
        if toggle_mqtt_topic != "":
            client.subscribe(
                        toggle_mqtt_topic,
                    )
    
    if gpio_type == 'INPUT':
        mqtt_message            = config[section]['MQTT_MESSAGE']
        mqtt_message_prcoessor  = config[section]['MQTT_MESSAGE_PROCESSOR']

        GPIO.setup(
                    gpio_pin,
                    GPIO.IN,
                    )
        gpio_val = GPIO.input(gpio_pin)
        client.publish(
                            topic=mqtt_topic, 
                            payload=mqtt_message.replace('{VALUE}',str(gpio_val) ),
                            qos=mqtt_qos,
                            retain=mqtt_retain,
                            )
        gpio_pin_state  = gpio_val

    gpioConfigs.append( {
                            'MQTT_TOPIC':           mqtt_topic,
                            'TOGGLE_MQTT_TOPIC':    toggle_mqtt_topic,
                            'TOGGLE_MQTT_MESSAGE':  toggle_mqtt_message,
                            'GPIO_PIN':             gpio_pin,
                            'GPIO_TYPE':            gpio_type,
                            'MQTT_PARSER':          mqtt_parser,
                            'MQTT_PARSER_ARG1':     mqtt_parser_arg1,
                            'MQTT_MESSAGE':         mqtt_message,
                            'GPIO_PIN_STATE':       gpio_pin_state,
                            'LOG_MESSAGE':          log_message,
                            'MQTT_QOS':             mqtt_qos,
                            'MQTT_RETAIN':          mqtt_retain,
                            } )
    logger.debug( 'Added configuration for %s' % (gpioConfigs[-1]) )


"""
The main loop of the program

Enter the loop of the MQTT
Check any GPIO inputs for state changes
"""
while True:
    client.loop( mqtt_loop_delay )

    for gpio in gpioConfigs:
        if gpio['GPIO_TYPE'] == 'INPUT':
            gpio_current_val = GPIO.input( gpio['GPIO_PIN'] )
            if gpio_current_val != gpio['GPIO_PIN_STATE']:
                gpio['GPIO_PIN_STATE'] = gpio_current_val
                payload = payload=gpio['MQTT_MESSAGE'].replace( '{VALUE}', str(gpio_current_val) )
                client.publish(
                                topic=gpio['MQTT_TOPIC'],
                                payload=payload,
                                qos=gpio['MQTT_QOS'],
                                retain=gpio['MQTT_RETAIN'],
                        )
                logger.info(gpio['LOG_MESSAGE'] % { 'message': payload, 'topic': gpio['MQTT_TOPIC'] })

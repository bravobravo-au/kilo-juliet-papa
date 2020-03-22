# kilo-juliet-papa
Control Raspberry Pi Outputs via MQTT

This python project can control Raspberry Pi GPIO Output pins as a result of receiving MQTT messages and also take GPIO inputs and deliver their status via MQTT. So a MQTT to GPIO bridge. Configuration is supplied via INI file and this allows one MQTT topic to be assigned to one GPIO. There is also the ability to configure how the software should decode the MQTT message to control the GPIO output.

At the moment the idea is to keep this fairly simple but you never know it might evolve from there as people provide feedback and feature requests.

Installation

1. Install the requirements

pip install -r requirements.txt

2. Edit your config.ini to your liking

3. Run kilo-juliet-papa

python kilo-juliet-papa.py


All configuration is supplied by the config.ini file. This means that you should not need to make changes to code to perform basic takss.

Sample output configuration

;Relay on BCM GPIO 17 with Message of ON or OFF
[RELAY1]
GPIO_TYPE=OUTPUT
GPIO_PIN=17
MQTT_TOPIC=STAT/relay1
TOGGLE_MQTT_TOPIC=STAT/relay1-toggle
TOGGLE_MQTT_MESSAGE={"Value":"{VALUE}"}
MQTT_PARSER=JSONINT
MQTT_PARSER_ARG1=Value
LOG_MESSAGE=Setting pin: %(pin)s to value: %(value)s based upon message: %(message)s on MQTT topic: %(topic)s
MQTT_QOS=0
MQTT_RETAIN=True

Outputs can listen on two MQTT topics. The main topic takes a value from the message that is published and this is used to set the Raspbery Pi output. The toggle topic will toggle the GPIO output everytime a message of any value is published to this topic.

The toggle mqtt message is the message that is published to MQTT_TOPIC when the output is toggled.

MQTT_PARSER allows different functions to be called to parse the MQTT message and change the output. JSONINT parses a JSON message for an integer assigned to JSON field defined in MQTT_PARSER_ARG1. All non zero values result in the output being High. A zero sets the output LOW. STRONOFF looks for the Strings ON and OFF to turn the output ON and OFF respectively.

LOG_MESSAGE is the string that is posted to the LOG file when this output is triggered.

Sample input configuration

[INPUT1]
GPIO_TYPE=INPUT
GPIO_PIN=2
MQTT_TOPIC=STAT/input1
MQTT_MESSAGE={"Value":"{VALUE}"}
MQTT_QOS=0
MQTT_RETAIN=True
LOG_MESSAGE=Published MQTT Message: %(message)s to topic: %(topic)s

MQTT_MESSAGE is the message that is posted to MQTT. {VALUE} is the logic value of the input.

Why the name?

Well applying the Nato Phonetic Alphabet to the name gives you KJP, which are the initials of the great Singer / Songwriter and guitarist Kelly Joe Phelps https://en.wikipedia.org/wiki/Kelly_Joe_Phelps



# kilo-juliet-papa
Control Raspberry Pi Outputs via MQTT

This python project can currently control Raspberry Pi GPIO pins as a result of receiving MQTT messages. Configuration is supplied via INI file and this allows one MQTT topic to be assigned to one GPIO. There is also the ability to configure how the software should decode the MQTT message to control the GPIO output.

At the moment the idea is to keep this fairly simple but you never know it might evolve from there as people provide feedback and feature requests.

Installation

1. Install the requirements

pip install -r requirements.txt

2. Edit your config.ini to your liking

3. Run kilo-juliet-papa

python kilo-juliet-papa.py


Why the name?

Well applying the Nato Phonetic Alphabet to the name gives you KJP, which are the initials of the great Singer / Songwriter and guitarist Kelly Joe Phelps https://en.wikipedia.org/wiki/Kelly_Joe_Phelps



#!/bin/env python
# -*- coding: utf-8 -*-
import sys
import ConfigParser
import call_forward_switcher_dcm

if len(sys.argv) <= 1:
    sys.exit("argv error")
forward_to_phone_number = sys.argv[1]

config = ConfigParser.ConfigParser()
config.read('switch.cfg')

switch_result = call_forward_switcher_dcm.call_forward_switch(
    twilio_sid=config.get("config", "twilio_sid"),
    twilio_token=config.get("config", "twilio_token"),
    call_from_phone_number=config.get("config", "call_from_phone_number"),
    call_to_phone_number=config.get("config", "call_to_phone_number"),
    forward_from_phone_number=config.get("config", "forward_from_phone_number"),
    forward_from_network_pass=config.get("config", "forward_from_network_pass"),
    forward_to_phone_number=forward_to_phone_number,
    record_entire=config.getboolean("config", "record_entire"),
    record_response=config.getboolean("config", "record_response"))

print(switch_result)

#!/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import ConfigParser
import call_forward_switcher_dcm

if len(sys.argv) <= 1:
    sys.exit("argv error")
forward_to_phone_number = sys.argv[1]

config = ConfigParser.ConfigParser()
config.read('switch.cfg')

print("Call forward switching... (it takes a minute)")
call_result = call_forward_switcher_dcm.call_forward_switch(
    twilio_sid=config.get("config", "twilio_sid"),
    twilio_token=config.get("config", "twilio_token"),
    twilio_phone_number=config.get("config", "twilio_phone_number"),
    transfer_service_dcm_phone_number=config.get("config", "transfer_service_dcm_phone_number"),
    forward_from_phone_number=config.get("config", "forward_from_phone_number"),
    forward_from_network_pass=config.get("config", "forward_from_network_pass"),
    forward_to_phone_number=forward_to_phone_number,
    record_entire=config.getboolean("config", "record_entire"),
    record_response=config.getboolean("config", "record_response"))

if call_result["error"]:
    print(call_result["error"].message)
    exit(1)

call_sid = call_result["sid"]
finished = False
wait_max = 12
for i in xrange(wait_max):
    status = call_forward_switcher_dcm.outbound_check_call_and_recordings_finished(
        twilio_sid=config.get("config", "twilio_sid"),
        twilio_token=config.get("config", "twilio_token"),
        call_sid = call_sid)
    if status["error"]:
        print(status["error"].message)
        exit(1)
    print "({}/{}) Call status: {}, Recordings status: {}".format(i + 1, wait_max, status["call_status"], status["recording_status"])
    if status["finished"]:
        finished = True
        break
    time.sleep(10)

if not finished:
    print("timed out")
    exit(1)

recordings_result = call_forward_switcher_dcm.outbound_retreive_recordings(
    twilio_sid=config.get("config", "twilio_sid"),
    twilio_token=config.get("config", "twilio_token"),
    call_sid = call_sid)
if recordings_result["error"]:
    print(recordings_result["error"].message)
    exit(1)

print("Call finished. rec1:[{}] rec2:[{}]".format(recordings_result["recording_number_confirm_sid"], recordings_result["recording_transfer_done_sid"]))

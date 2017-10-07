#!/bin/env python
# -*- coding: utf-8 -*-
import sys
import time
import argparse
import ConfigParser
import call_forward_switcher_dcm

def main():
    parser = argparse.ArgumentParser("call-forward-switcher-dcm.py")
    parser.add_argument("--forwardto", dest="forward_to_phone_number",
        required=True,
        help="Phone number to be forwarded to")
    parser.add_argument("--config", dest="config_file_name",
        default="switch.cfg",
        help="Config file name")
    args = parser.parse_args()

    forward_to_phone_number = args.forward_to_phone_number
    config = ConfigParser.ConfigParser()
    config.read(args.config_file_name)

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
        return 1

    call_sid = call_result["sid"]
    finished = False
    wait_max = 24
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
        time.sleep(5)

    if not finished:
        print("timed out")
        return 1

    recordings_result = call_forward_switcher_dcm.outbound_retreive_recordings(
        twilio_sid=config.get("config", "twilio_sid"),
        twilio_token=config.get("config", "twilio_token"),
        call_sid = call_sid)
    if recordings_result["error"]:
        print(recordings_result["error"].message)
        return 1

    print("Call finished. rec1:[{}] rec2:[{}]".format(recordings_result["recording_number_confirm_sid"], recordings_result["recording_switch_done_sid"]))

    number_confirm = call_forward_switcher_dcm.check_recording_number_confirm(
        twilio_sid=config.get("config", "twilio_sid"),
        recording_number_confirm_sid=recordings_result["recording_number_confirm_sid"],
        google_api_key=config.get("config", "google_api_key"),
        forward_to_phone_number=forward_to_phone_number)

    if number_confirm["error"]:
        print(number_confirm["error"].message)
        return 1

    if not number_confirm["check"]:
        print("Number confirm check Error")
        return 1

    print("Number confirm check OK")

    switch_done = call_forward_switcher_dcm.check_recording_switch_done(
        twilio_sid=config.get("config", "twilio_sid"),
        recording_switch_done_sid=recordings_result["recording_switch_done_sid"],
        google_api_key=config.get("config", "google_api_key"))

    if switch_done["error"]:
        print(switch_done["error"].message)
        return 1

    if not switch_done["check"]:
        print("Switch done check Error")
        return 1

    print("Switch done check OK")

    print("Call forward switch success. Current forward to:{}".format(str(forward_to_phone_number)))
    return 0

if __name__ == '__main__':
    res = main()
    exit(res)

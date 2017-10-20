#!/bin/env python
# -*- coding: utf-8 -*-
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

    def verbose_message(message):
        print(message)
    call_result = call_forward_switcher_dcm.call_forward_switch_batch(
        twilio_sid=config.get("config", "twilio_sid"),
        twilio_token=config.get("config", "twilio_token"),
        twilio_phone_number=config.get("config", "twilio_phone_number"),
        transfer_service_dcm_phone_number=config.get("config", "transfer_service_dcm_phone_number"),
        forward_from_phone_number=config.get("config", "forward_from_phone_number"),
        forward_from_network_pass=config.get("config", "forward_from_network_pass"),
        forward_to_phone_number=forward_to_phone_number,
        record_entire=config.getboolean("config", "record_entire"),
        record_response=config.getboolean("config", "record_response"),
        google_api_key=config.get("config", "google_api_key"),
        verbose_message_lambda=verbose_message)

    if call_result["error"]:
        print(call_result["message"])
        return 1

    print("Call forward switch success. Current forward to:{}".format(str(forward_to_phone_number)))
    return 0

if __name__ == '__main__':
    res = main()
    exit(res)

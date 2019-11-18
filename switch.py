#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import configparser
import call_forward_switcher_jp

def main():
    parser = argparse.ArgumentParser("switch.py")
    parser.add_argument("--career", dest="mobile_career",
        required=True,
        help="Mobile career [dcm] or [auk]")
    parser.add_argument("--forwardto", dest="forward_to_phone_number",
        required=True,
        help="Phone number to be forwarded to")
    parser.add_argument("--config", dest="config_file_name",
        default="switch.cfg",
        help="Config file name")
    args = parser.parse_args()

    forward_to_phone_number = args.forward_to_phone_number
    mobile_career = args.mobile_career
    config = configparser.ConfigParser()
    config.read(args.config_file_name)

    if mobile_career != "dcm" and mobile_career != "auk":
        print("--career parameters must be [dcm] or [auk]")
        exit(1)

    print("Call forward switching... (it takes a minute)")

    def verbose_message(message):
        print(message)
    
    config_section_name = "config"
    call_param = {
        'career': mobile_career,
        'twilio_sid': config.get(config_section_name, "twilio_sid"),
        'twilio_token': config.get(config_section_name, "twilio_token"),
        'twilio_phone_number': config.get(config_section_name, "twilio_phone_number"),
        'forward_from_phone_number': config.get(config_section_name, "forward_from_phone_number"),
        'forward_from_network_pass': config.get(config_section_name, "forward_from_network_pass"),
        'forward_to_phone_number': forward_to_phone_number,
        'record_entire': config.getboolean(config_section_name, "record_entire"),
        'record_response': config.getboolean(config_section_name, "record_response"),
        'google_api_key': config.get(config_section_name, "google_api_key"),
        'verbose_message_lambda': verbose_message,
    }

    if mobile_career == "dcm":
        call_param['transfer_service_career_phone_number'] = config.get(config_section_name, "transfer_service_dcm_phone_number")
    elif mobile_career == "auk":
        call_param['transfer_service_career_phone_number'] = config.get(config_section_name, "transfer_service_auk_phone_number")
    call_result = call_forward_switcher_jp.call_forward_switch_batch(**call_param)
    
    if call_result["error"]:
        print(call_result["message"])
        return 1

    print("Call forward switch success. Current forward to:{}".format(str(forward_to_phone_number)))
    return 0

if __name__ == '__main__':
    res = main()
    exit(res)

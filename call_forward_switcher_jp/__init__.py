# -*- coding: utf-8 -*-
import call_forward_switcher_jp.dcm
import call_forward_switcher_jp.auk

def call_forward_switch_batch(career, twilio_sid, twilio_token, twilio_phone_number, transfer_service_career_phone_number,
    forward_from_phone_number, forward_from_network_pass, forward_to_phone_number,
    record_entire, record_response, google_api_key,
    verbose_message_lambda=None, wait_limit_sec=180, wait_sleep=5):

    if career == "dcm":
        return call_forward_switcher_jp.dcm.call_forward_switch_batch(
            twilio_sid=twilio_sid,
            twilio_token=twilio_token,
            twilio_phone_number=twilio_phone_number,
            transfer_service_dcm_phone_number=transfer_service_career_phone_number,
            forward_from_phone_number=forward_from_phone_number,
            forward_from_network_pass=forward_from_network_pass,
            forward_to_phone_number=forward_to_phone_number,
            record_entire=record_entire,
            record_response=record_response,
            google_api_key=google_api_key,
            verbose_message_lambda=verbose_message_lambda,
            wait_limit_sec=wait_limit_sec,
            wait_sleep=wait_sleep)
    elif career == "auk":
        return call_forward_switcher_jp.auk.call_forward_switch_batch(
            twilio_sid=twilio_sid,
            twilio_token=twilio_token,
            twilio_phone_number=twilio_phone_number,
            transfer_service_auk_phone_number=transfer_service_career_phone_number,
            forward_from_phone_number=forward_from_phone_number,
            forward_from_network_pass=forward_from_network_pass,
            forward_to_phone_number=forward_to_phone_number,
            record_entire=record_entire,
            record_response=record_response,
            google_api_key=google_api_key,
            verbose_message_lambda=verbose_message_lambda,
            wait_limit_sec=wait_limit_sec,
            wait_sleep=wait_sleep)
    else:
        raise ValueError("invalid career value. expected=dcm or auk")

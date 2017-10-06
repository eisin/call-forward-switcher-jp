# -*- coding: utf-8 -*-
import twilio.rest
from twilio.base.exceptions import TwilioRestException
import urllib

def call_forward_switch(twilio_sid, twilio_token, twilio_phone_number, transfer_service_dcm_phone_number,
    forward_from_phone_number, forward_from_network_pass, forward_to_phone_number,
    record_entire, record_response):

    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not twilio_token:
        raise ValueError("twilio_token is missing")
    if not twilio_phone_number:
        raise ValueError("twilio_phone_number is missing")
    if not transfer_service_dcm_phone_number:
        raise ValueError("transfer_service_dcm_phone_number is missing")
    if not forward_from_phone_number:
        raise ValueError("forward_from_phone_number is missing")
    if not forward_from_phone_number.isdigit() or len(forward_from_phone_number) != 11:
        raise ValueError("forward_from_phone_number is not valid form '09000000000'")
    if not forward_from_network_pass:
        raise ValueError("forward_from_network_pass is missing")
    if not forward_from_network_pass.isdigit() or len(forward_from_network_pass) != 4:
        raise ValueError("forward_from_network_pass is not valid form '0000'")
    if not forward_to_phone_number:
        raise ValueError("forward_to_phone_number is missing")
    if not forward_to_phone_number.isdigit() or len(forward_to_phone_number) != 11:
        raise ValueError("forward_to_phone_number is not valid form '09000000000'")

    twilio_client = twilio.rest.Client(twilio_sid, twilio_token)

    if record_response:
        twiml_hangup = """
            <Response>
                <Hangup/>
            </Response>
        """
        url_hangup="http://twimlets.com/echo?Twiml=" + urllib.quote(twiml_hangup)

        twiml_confirm = """
            <Response>
                <Say>e</Say>
                <Play digits="#"/>
                <Say>e</Say>
                <Record playBeep="false" timeout="5" maxLength="5" action="{}"/>
            </Response>
        """.format(url_hangup)
        url_confirm="http://twimlets.com/echo?Twiml=" + urllib.quote(twiml_confirm)

        twiml = """
            <Response>
                <Pause length="6"/>
                <Say>a</Say>
                <Play digits="{}"/>
                <Say>a</Say>
                <Pause length="3"/>
                <Say>b</Say>
                <Play digits="{}"/>
                <Say>b</Say>
                <Pause length="4"/>
                <Say>c</Say>
                <Play digits="3"/>
                <Say>c</Say>
                <Pause length="5"/>
                <Say>d</Say>
                <Play digits="{}"/>
                <Say>d</Say>
                <Record playBeep="false" timeout="16" maxLength="16" trim="trim-silence" action="{}"/>
            </Response>
        """.format(forward_from_phone_number, forward_from_network_pass, forward_to_phone_number, url_confirm)
    else:
        twiml = """
            <Response>
                <Pause length="6"/>
                <Say>a</Say>
                <Play digits="{}"/>
                <Say>a</Say>
                <Pause length="3"/>
                <Say>b</Say>
                <Play digits="{}"/>
                <Say>b</Say>
                <Pause length="4"/>
                <Say>c</Say>
                <Play digits="3"/>
                <Say>c</Say>
                <Pause length="5"/>
                <Say>d</Say>
                <Play digits="{}"/>
                <Say>d</Say>
                <Pause length="16"/>
                <Say>e</Say>
                <Play digits="#"/>
                <Say>e</Say>
                <Pause length="5"/>
                <Hangup/>
            </Response>
        """.format(forward_from_phone_number, forward_from_network_pass, forward_to_phone_number)

    call_record_opt = "false"
    if record_entire:
        call_record_opt = "true"

    try:
        call = twilio_client.calls.create(
            to=transfer_service_dcm_phone_number,
            from_=twilio_phone_number,
            url="http://twimlets.com/echo?Twiml=" + urllib.quote(twiml),
            record=call_record_opt,
        )
    except TwilioRestException as e:
        return { "sid": None, "call": None, "error": e }

    return { "sid": call.sid, "call": call, "error": None}

def outbound_check_call_finished(twilio_sid, twilio_token, call_sid):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not twilio_token:
        raise ValueError("twilio_token is missing")
    if not call_sid:
        raise ValueError("call_sid is missing")

    twilio_client = twilio.rest.Client(twilio_sid, twilio_token)

    try:
        call = twilio_client.calls(call_sid).fetch()
    except TwilioRestException as e:
        return { "finished": True, "status": None, "call": None, "error": e }

    if call.status in {"queued", "ringing", "in-progress"}:
        return { "finished": False, "status": call.status, "call": call, "error": None }
    else:
        return { "finished": True, "status": call.status, "call": call, "error": None }

def outbound_check_call_and_recordings_finished(twilio_sid, twilio_token, call_sid):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not twilio_token:
        raise ValueError("twilio_token is missing")
    if not call_sid:
        raise ValueError("call_sid is missing")

    twilio_client = twilio.rest.Client(twilio_sid, twilio_token)

    try:
        call = twilio_client.calls(call_sid).fetch()
    except TwilioRestException as e:
        return { "finished": None, "call_status": None, "recording_status": None, "error": e }

    if call.status in {"queued", "ringing", "in-progress"}:
        return { "finished": False, "call_status": call.status, "recording_status": None, "error": None }

    try:
        recordings = twilio_client.recordings.list(call_sid=call_sid)
    except TwilioRestException as e:
        return { "finished": None, "call_status": None, "recording_status": None, "error": e }

    recording_status = None
    for recording in recordings:
        recording_status = recording.status
        if recording_status != "completed":
            return { "finished": False, "call_status": call.status, "recording_status": recording_status, "error": None }

    return { "finished": True, "call_status": call.status, "recording_status": recording_status, "error": None }

def outbound_retreive_recordings(twilio_sid, twilio_token, call_sid):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not twilio_token:
        raise ValueError("twilio_token is missing")
    if not call_sid:
        raise ValueError("call_sid is missing")

    twilio_client = twilio.rest.Client(twilio_sid, twilio_token)

    try:
        recordings = twilio_client.recordings.list(call_sid=call_sid)
    except TwilioRestException as e:
        return { "recording_number_confirm_sid": None, "recording_transfer_done_sid": None, "recordings": None, "error": e }

    recording_number_confirm_sid = None
    recording_transfer_done_sid = None
    for recording in recordings:
        duration = int(recording.duration)
        if 10 - 1 <= duration and duration <= 16 + 1:
            recording_number_confirm_sid = recording.sid
        if 5 - 1 <= duration and duration <= 5 + 1:
            recording_transfer_done_sid = recording.sid
    return {
        "recording_number_confirm_sid": recording_number_confirm_sid,
        "recording_transfer_done_sid": recording_transfer_done_sid,
        "recordings": recordings,
        "error": None,
    }


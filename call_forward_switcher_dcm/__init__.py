# -*- coding: utf-8 -*-
import twilio.rest
from twilio.base.exceptions import TwilioRestException
import urllib
import urllib2
import base64
import json
import time

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
        return { "recording_number_confirm_sid": None, "recording_switch_done_sid": None, "recordings": None, "error": e }

    recording_number_confirm_sid = None
    recording_switch_done_sid = None
    for recording in recordings:
        duration = int(recording.duration)
        if 10 - 1 <= duration and duration <= 16 + 1:
            recording_number_confirm_sid = recording.sid
        if 5 - 1 <= duration and duration <= 5 + 1:
            recording_switch_done_sid = recording.sid
    return {
        "recording_number_confirm_sid": recording_number_confirm_sid,
        "recording_switch_done_sid": recording_switch_done_sid,
        "recordings": recordings,
        "error": None,
    }

def check_recording_number_confirm(twilio_sid, twilio_token, recording_number_confirm_sid, google_api_key, forward_to_phone_number):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not recording_number_confirm_sid:
        raise ValueError("recording_number_confirm_sid is missing")
    if not google_api_key:
        raise ValueError("google_api_key is missing")
    if not forward_to_phone_number:
        raise ValueError("forward_to_phone_number is missing")
    if not forward_to_phone_number.isdigit() or len(forward_to_phone_number) != 11:
        raise ValueError("forward_to_phone_number is not valid form '09000000000'")
    try:
        passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passmgr.add_password(None, "https://api.twilio.com/2010-04-01/", twilio_sid, twilio_token)
        opener = urllib2.build_opener(urllib2.HTTPSHandler(), urllib2.HTTPBasicAuthHandler(passmgr))
        urlrec = opener.open("https://api.twilio.com/2010-04-01/Accounts/{}/Recordings/{}.wav".format(twilio_sid, recording_number_confirm_sid), timeout=30)
    except urllib2.HTTPError as e:
        return { "check": False, "recognize": None, "error": e }
    wavedata = urlrec.read()
    wavedata_base64url = base64.b64encode(wavedata).replace("+", "-").replace("/", "_")
    query = json.dumps({
        "config": {
            "encoding": u"LINEAR16",
            "languageCode": u"ja-JP",
            "maxAlternatives": 20,
            "speechContexts": [
                {
                    "phrases": [
                        u"転送",
                        u"先",
                        u"電話番号に",
                        u"を登録します",
                        u"0",
                        u"1",
                        u"2",
                        u"3",
                        u"4",
                        u"5",
                        u"6",
                        u"7",
                        u"8",
                        u"9",
                        u"登録番号が",
                        u"誤っています",
                        u"転送先電話番号を",
                        u"登録してください",
                    ]
                }
            ]
        },
        "audio": {
            "content": wavedata_base64url,
        }
    })

    request = urllib2.Request("https://speech.googleapis.com/v1/speech:recognize?key={}".format(google_api_key))
    request.add_header("Content-Type", "application/json")
    request.add_header("Content-Length", len(query))
    request.add_data(query)

    try:
        urlrecognize = urllib2.urlopen(request, timeout=30)
        result = urlrecognize.read()
    except urllib2.HTTPError as e:
        return { "check": False, "recognize": None, "transcript": None, "result_text": None, "error": e }

    js = json.loads(result, "utf-8")
    transcript = js['results'][0]['alternatives'][0]['transcript']
    if result.find(str(forward_to_phone_number)) < 0:
        return { "check": False, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

    return { "check": True, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

def check_recording_switch_done(twilio_sid, twilio_token, recording_switch_done_sid, google_api_key):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not recording_switch_done_sid:
        raise ValueError("recording_switch_done_sid is missing")
    if not google_api_key:
        raise ValueError("google_api_key is missing")
    try:
        passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passmgr.add_password(None, "https://api.twilio.com/2010-04-01/", twilio_sid, twilio_token)
        opener = urllib2.build_opener(urllib2.HTTPSHandler(), urllib2.HTTPBasicAuthHandler(passmgr))
        urlrec = opener.open("https://api.twilio.com/2010-04-01/Accounts/{}/Recordings/{}.wav".format(twilio_sid, recording_switch_done_sid), timeout=30)
    except urllib2.HTTPError as e:
        return { "check": False, "recognize": None, "error": e }
    wavedata = urlrec.read()
    wavedata_base64url = base64.b64encode(wavedata).replace("+", "-").replace("/", "_")
    query = json.dumps({
        "config": {
            "encoding": u"LINEAR16",
            "languageCode": u"ja-JP",
            "maxAlternatives": 20,
            "speechContexts": [
                {
                    "phrases": [
                        u"設定",
                        u"いたしました",
                        u"メイン",
                        u"メニュー",
                        u"です",
                    ]
                }
            ]
        },
        "audio": {
            "content": wavedata_base64url,
        }
    })

    request = urllib2.Request("https://speech.googleapis.com/v1/speech:recognize?key={}".format(google_api_key))
    request.add_header("Content-Type", "application/json")
    request.add_header("Content-Length", len(query))
    request.add_data(query)

    try:
        urlrecognize = urllib2.urlopen(request, timeout=30)
        result = unicode(urlrecognize.read(), "utf-8")
    except urllib2.HTTPError as e:
        return { "check": False, "recognize": None, "transcript": None, "result_text": None, "error": e }

    js = json.loads(result, "utf-8")
    transcript = js['results'][0]['alternatives'][0]['transcript']
    if result.find(u"設定いたしました") < 0 and \
        result.find(u"設定致しました") < 0 and \
        result.find(u"設定しました") < 0:
        return { "check": False, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

    return { "check": True, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

def call_forward_switch_batch(twilio_sid, twilio_token, twilio_phone_number, transfer_service_dcm_phone_number,
    forward_from_phone_number, forward_from_network_pass, forward_to_phone_number,
    record_entire, record_response, google_api_key,
    verbose_message_lambda=None, wait_limit_sec=120, wait_sleep=5):

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
    if not google_api_key:
        raise ValueError("google_api_key is missing")

    call_sid = None
    recording_number_confirm_sid = None
    recording_switch_done_sid = None

    call_result = call_forward_switch(
        twilio_sid=twilio_sid,
        twilio_token=twilio_token,
        twilio_phone_number=twilio_phone_number,
        transfer_service_dcm_phone_number=transfer_service_dcm_phone_number,
        forward_from_phone_number=forward_from_phone_number,
        forward_from_network_pass=forward_from_network_pass,
        forward_to_phone_number=forward_to_phone_number,
        record_entire=record_entire,
        record_response=record_response)

    call_sid = call_result["sid"]
    if call_result["error"]:
        return {
            "error": call_result["error"],
            "message": call_result["error"].message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    finished = False
    current_wait_sec = 0
    while current_wait_sec <= wait_limit_sec:
        status = outbound_check_call_and_recordings_finished(
            twilio_sid=twilio_sid,
            twilio_token=twilio_token,
            call_sid=call_sid)
        if status["error"]:
            return {
                "error": status["error"],
                "message": status["error"].message,
                "call_sid": call_sid,
                "recording_number_confirm_sid": recording_number_confirm_sid,
                "recording_switch_done_sid": recording_switch_done_sid,
            }
        verbose_message_lambda(message=u"({}/{}) Call status: {}, Recordings status: {}".format(current_wait_sec, wait_limit_sec, status["call_status"], status["recording_status"]))
        if status["finished"]:
            finished = True
            break
        current_wait_sec += wait_sleep
        time.sleep(wait_sleep)

    if not finished:
        error = Exception('Call timed out. call_sid:[{}]'.message(call_sid))
        return {
            "error": error,
            "message": error.message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    recordings_result = outbound_retreive_recordings(
        twilio_sid=twilio_sid,
        twilio_token=twilio_token,
        call_sid=call_sid)
    if recordings_result["error"]:
        return {
            "error": recordings_result["error"],
            "message": recordings_result["error"].message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    verbose_message_lambda(message=u"Call finished. rec1:[{}] rec2:[{}]".format(recordings_result["recording_number_confirm_sid"], recordings_result["recording_switch_done_sid"]))
    recording_number_confirm_sid = recordings_result["recording_number_confirm_sid"]
    recording_switch_done_sid = recordings_result["recording_switch_done_sid"]

    number_confirm = check_recording_number_confirm(
        twilio_sid=twilio_sid,
        twilio_token=twilio_token,
        recording_number_confirm_sid=recording_number_confirm_sid,
        google_api_key=google_api_key,
        forward_to_phone_number=forward_to_phone_number)

    if number_confirm["error"]:
        return {
            "error": number_confirm["error"],
            "message": number_confirm["error"].message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    if not number_confirm["check"]:
        error = Exception(u"Number confirm check Error [{}]".format(number_confirm["transcript"]))
        return {
            "error": error,
            "message": error.message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    verbose_message_lambda(message=u"Number confirm check OK [{}]".format(number_confirm["transcript"]))

    switch_done = check_recording_switch_done(
        twilio_sid=twilio_sid,
        twilio_token=twilio_token,
        recording_switch_done_sid=recording_switch_done_sid,
        google_api_key=google_api_key)

    if switch_done["error"]:
        error = Exception(u"Number confirm check Error [{}]".format(number_confirm["transcript"]))
        return {
            "error": switch_done["error"],
            "message": switch_done["error"].message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    if not switch_done["check"]:
        error = Exception(u"Switch done check Error [{}]".format(switch_done["transcript"]))
        return {
            "error": error,
            "message": error.message,
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    verbose_message_lambda(message=u"Switch done check OK [{}]".format(switch_done["transcript"]))

    return {
        "error": None,
        "message": u"Call forward switch success. Current forward to:{}".format(str(forward_to_phone_number)),
        "call_sid": call_sid,
        "recording_number_confirm_sid": recording_number_confirm_sid,
        "recording_switch_done_sid": recording_switch_done_sid,
    }

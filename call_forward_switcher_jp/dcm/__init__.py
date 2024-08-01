# -*- coding: utf-8 -*-
import twilio.rest
from twilio.base.exceptions import TwilioRestException
import urllib
import urllib.request
import base64
import json
import time
import re


def _xml_shorten(original_xml_text):
    text = original_xml_text
    text = re.sub(r"^\s+", "", text, 0, re.MULTILINE)
    text = re.sub(r"\n", "", text)
    return text

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
    if not forward_to_phone_number.isdigit() or len(forward_to_phone_number) < 6 or 12 < len(forward_to_phone_number):
        raise ValueError("forward_to_phone_number is not valid form")

    twilio_client = twilio.rest.Client(twilio_sid, twilio_token)

    if record_response:
        twiml_hangup = """
            <Response>
                <Hangup/>
            </Response>
        """
        url_hangup="http://twimlets.com/echo?Twiml=" + urllib.parse.quote(_xml_shorten(twiml_hangup))

        twiml_confirm = """
            <Response>
                <Say>e</Say>
                <Play digits="#"/>
                <Say>e</Say>
                <Record playBeep="false" timeout="0" maxLength="5" action="{}"/>
                <Say>f</Say>
            </Response>
        """.format(url_hangup)
        url_confirm="http://twimlets.com/echo?Twiml=" + urllib.parse.quote(_xml_shorten(twiml_confirm))

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
                <Record playBeep="false" timeout="0" maxLength="19" trim="trim-silence" action="{}"/>
            </Response>
        """.format(forward_from_phone_number, forward_from_network_pass, forward_to_phone_number, url_confirm)
        twiml = _xml_shorten(twiml)
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
                <Say>f</Say>
                <Hangup/>
            </Response>
        """.format(forward_from_phone_number, forward_from_network_pass, forward_to_phone_number)
        twiml = _xml_shorten(twiml)

    call_record_opt = "false"
    if record_entire:
        call_record_opt = "true"

    try:
        call = twilio_client.calls.create(
            to=transfer_service_dcm_phone_number,
            from_=twilio_phone_number,
            url="http://twimlets.com/echo?Twiml=" + urllib.parse.quote(twiml),
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
        if 10 - 1 <= duration and duration <= 19 + 1:
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
    if not forward_to_phone_number.isdigit() or len(forward_to_phone_number) < 6 or 12 < len(forward_to_phone_number):
        raise ValueError("forward_to_phone_number is not valid form")
    try:
        passmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passmgr.add_password(None, "https://api.twilio.com/2010-04-01/", twilio_sid, twilio_token)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(), urllib.request.HTTPBasicAuthHandler(passmgr))
        urlrec = opener.open("https://api.twilio.com/2010-04-01/Accounts/{}/Recordings/{}.wav".format(twilio_sid, recording_number_confirm_sid), timeout=30)
    except urllib.error.HTTPError as e:
        return { "check": False, "recognize": None, "error": e }
    wavedata = urlrec.read()
    wavedata_base64url = base64.urlsafe_b64encode(wavedata).decode('utf-8')
    query = json.dumps({
        "config": {
            "encoding": u"LINEAR16",
            "languageCode": u"ja-JP",
            "maxAlternatives": 20,
            "model": u"telephony",
            "speechContexts": [
                {
                    "phrases": [
                        u"転送",
                        u"先",
                        u"電話番号に",
                        u"を登録します",
                        u"$FULLPHONENUM",
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

    request = urllib.request.Request(url="https://speech.googleapis.com/v1/speech:recognize?key={}".format(google_api_key), data=query.encode('utf-8'))
    request.add_header("Content-Type", "application/json")
    request.add_header("Content-Length", len(query))

    try:
        urlrecognize = urllib.request.urlopen(request, timeout=30)
        result = urlrecognize.read()
    except urllib.error.HTTPError as e:
        return { "check": False, "recognize": None, "transcript": None, "result_text": None, "error": e }

    js = json.loads(result.decode('utf-8'))
    for speech_alternative in js['results'][0]['alternatives']:
        transcript = speech_alternative["transcript"]
        transcript_numberonly = u"".join(re.findall(r'[0-9]+', transcript))
        # 電話番号チェックは必ずしも必須としない。
        # Google Speech-To-Textの精度が2024年1月より落ちており、番号の認識が不正確となったため。
        if transcript_numberonly.find(str(forward_to_phone_number)) >= 0 or \
           transcript.find(u"登録します") >= 0:
            return { "check": True, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

    return { "check": False, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

def check_recording_switch_done(twilio_sid, twilio_token, recording_switch_done_sid, google_api_key):
    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not recording_switch_done_sid:
        raise ValueError("recording_switch_done_sid is missing")
    if not google_api_key:
        raise ValueError("google_api_key is missing")
    try:
        passmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        passmgr.add_password(None, "https://api.twilio.com/2010-04-01/", twilio_sid, twilio_token)
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(), urllib.request.HTTPBasicAuthHandler(passmgr))
        urlrec = opener.open("https://api.twilio.com/2010-04-01/Accounts/{}/Recordings/{}.wav".format(twilio_sid, recording_switch_done_sid), timeout=30)
    except urllib.error.HTTPError as e:
        return { "check": False, "recognize": None, "error": e }
    wavedata = urlrec.read()
    wavedata_base64url = base64.urlsafe_b64encode(wavedata)
    query = json.dumps({
        "config": {
            "encoding": u"LINEAR16",
            "languageCode": u"ja-JP",
            "maxAlternatives": 20,
            "model": u"telephony",
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
            "content": wavedata_base64url.decode('utf-8'),
        }
    })

    request = urllib.request.Request(url="https://speech.googleapis.com/v1/speech:recognize?key={}".format(google_api_key), data=query.encode('utf-8'))
    request.add_header("Content-Type", "application/json")
    request.add_header("Content-Length", len(query))

    try:
        urlrecognize = urllib.request.urlopen(request, timeout=30)
        result = urlrecognize.read()
    except urllib.error.HTTPError as e:
        return { "check": False, "recognize": None, "transcript": None, "result_text": None, "error": e }

    js = json.loads(result.decode('utf-8'))
    for speech_alternative in js['results'][0]['alternatives']:
        transcript = speech_alternative["transcript"]
        if transcript.find(u"設定") >= 0 or \
            transcript.find(u"いたしました") >= 0 or \
            transcript.find(u"致しました") >= 0 or \
            transcript.find(u"しました") >= 0:
            return { "check": True, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

    return { "check": False, "recognize": result, "transcript": transcript, "result_text": result, "error": None }

def call_forward_switch_batch(twilio_sid, twilio_token, twilio_phone_number, transfer_service_dcm_phone_number,
    forward_from_phone_number, forward_from_network_pass, forward_to_phone_number,
    record_entire, record_response, google_api_key,
    verbose_message_lambda=None, wait_limit_sec=180, wait_sleep=5):

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
    if not forward_to_phone_number.isdigit() or len(forward_to_phone_number) < 6 or 12 < len(forward_to_phone_number):
        raise ValueError("forward_to_phone_number is not valid form")
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
            "message": str(call_result["error"]),
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
                "message": str(status["error"]),
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
        error = Exception('Call timed out. call_sid:[{}]'.format(call_sid))
        return {
            "error": error,
            "message": str(error),
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
            "message": str(recordings_result["error"]),
            "call_sid": call_sid,
            "recording_number_confirm_sid": recording_number_confirm_sid,
            "recording_switch_done_sid": recording_switch_done_sid,
        }

    verbose_message_lambda(message=u"Call finished. rec1:[{}] rec2:[{}]".format(recordings_result["recording_number_confirm_sid"], recordings_result["recording_switch_done_sid"]))
    recording_number_confirm_sid = recordings_result["recording_number_confirm_sid"]
    recording_switch_done_sid = recordings_result["recording_switch_done_sid"]

    if record_response:
        number_confirm = check_recording_number_confirm(
            twilio_sid=twilio_sid,
            twilio_token=twilio_token,
            recording_number_confirm_sid=recording_number_confirm_sid,
            google_api_key=google_api_key,
            forward_to_phone_number=forward_to_phone_number)

        if number_confirm["error"]:
            return {
                "error": number_confirm["error"],
                "message": str(number_confirm["error"]),
                "call_sid": call_sid,
                "recording_number_confirm_sid": recording_number_confirm_sid,
                "recording_switch_done_sid": recording_switch_done_sid,
            }

        if not number_confirm["check"]:
            error = Exception(u"Number confirm check Error [{}]".format(number_confirm["transcript"]))
            return {
                "error": error,
                "message": str(error),
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
                "message": str(switch_done["error"]),
                "call_sid": call_sid,
                "recording_number_confirm_sid": recording_number_confirm_sid,
                "recording_switch_done_sid": recording_switch_done_sid,
            }

        if not switch_done["check"]:
            error = Exception(u"Switch done check Error [{}]".format(switch_done["transcript"]))
            return {
                "error": error,
                "message": str(error),
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

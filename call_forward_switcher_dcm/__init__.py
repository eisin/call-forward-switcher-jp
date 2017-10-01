# -*- coding: utf-8 -*-
import twilio.rest
import urllib

def call_forward_switch(twilio_sid, twilio_token, call_from_phone_number, call_to_phone_number,
    forward_from_phone_number, forward_from_network_pass, forward_to_phone_number,
    record_entire, record_response):

    if not twilio_sid:
        raise ValueError("twilio_sid is missing")
    if not twilio_token:
        raise ValueError("twilio_token is missing")
    if not call_from_phone_number:
        raise ValueError("call_from_phone_number is missing")
    if not call_to_phone_number:
        raise ValueError("call_to_phone_number is missing")
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
    call = twilio_client.calls.create(
        to=call_to_phone_number,
        from_=call_from_phone_number,
        url="http://twimlets.com/echo?Twiml=" + urllib.quote(twiml),
        record=call_record_opt,
    )

    return call.sid
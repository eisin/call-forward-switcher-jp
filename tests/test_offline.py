# -*- coding: utf-8 -*-
"""
python3 -m unittest discover -s tests -v
"""
import json
import sys
import types
import unittest
from unittest import mock


def _install_twilio_stub():
    try:
        import twilio.rest  # noqa: F401
        import twilio.base.exceptions  # noqa: F401
        return
    except ImportError:
        pass
    twilio = types.ModuleType("twilio")
    rest = types.ModuleType("twilio.rest")
    base = types.ModuleType("twilio.base")
    exc = types.ModuleType("twilio.base.exceptions")

    class TwilioRestException(Exception):
        pass

    rest.Client = mock.MagicMock()
    exc.TwilioRestException = TwilioRestException
    twilio.rest = rest
    twilio.base = base
    base.exceptions = exc
    sys.modules.update({
        "twilio": twilio, "twilio.rest": rest,
        "twilio.base": base, "twilio.base.exceptions": exc,
    })


_install_twilio_stub()

import call_forward_switcher_jp as top  # noqa: E402
import call_forward_switcher_jp.dcm as dcm  # noqa: E402
from twilio.base.exceptions import TwilioRestException  # noqa: E402

FROM = "09000000000"
PASS = "1234"
TO = "0312345678"


def kwargs_for(mod, **over):
    key = "transfer_service_%s_phone_number" % mod.__name__.rsplit(".", 1)[1]
    kw = dict(
        twilio_sid="sid", twilio_token="tok", twilio_phone_number="+8150",
        forward_from_phone_number=FROM, forward_from_network_pass=PASS,
        forward_to_phone_number=TO, record_entire=False, record_response=False,
    )
    kw[key] = "+81570"
    kw.update(over)
    return kw


def twilio_error(msg):
    # 本物のTwilioRestExceptionは status, uri が必須
    return TwilioRestException(500, "/test", msg)


def rec(sid, duration):
    return types.SimpleNamespace(sid=sid, duration=str(duration), status="completed")


class _Base:
    mod = None

    def client(self):
        """twilio.rest.Clientをモックに差し替える。"""
        p = mock.patch.object(self.mod.twilio.rest, "Client")
        self.addCleanup(p.stop)
        return p.start().return_value


class CallForwardSwitchTests(_Base):
    def test_validation_errors(self):
        for field, value in [
            ("twilio_sid", ""), ("twilio_token", ""), ("twilio_phone_number", ""),
            ("forward_from_phone_number", ""), ("forward_from_phone_number", "090"),
            ("forward_from_phone_number", "0900000000a"),
            ("forward_from_network_pass", ""), ("forward_from_network_pass", "123"),
            ("forward_from_network_pass", "12a4"),
            ("forward_to_phone_number", ""), ("forward_to_phone_number", "12345"),
            ("forward_to_phone_number", "1" * 13),
        ]:
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    self.mod.call_forward_switch(**kwargs_for(self.mod, **{field: value}))

    def test_success_builds_call(self):
        c = self.client()
        c.calls.create.return_value = types.SimpleNamespace(sid="CA1")
        r = self.mod.call_forward_switch(**kwargs_for(self.mod, record_entire=True))
        self.assertEqual(r["sid"], "CA1")
        self.assertIsNone(r["error"])
        kw = c.calls.create.call_args.kwargs
        self.assertEqual(kw["from_"], "+8150")
        self.assertEqual(kw["record"], "true")
        self.assertTrue(kw["url"].startswith("http://twimlets.com/echo?Twiml="))
        for needle in (FROM, PASS, TO):
            self.assertIn(needle, kw["url"])

    def test_record_response_adds_record_verb(self):
        c = self.client()
        c.calls.create.return_value = types.SimpleNamespace(sid="CA1")
        self.mod.call_forward_switch(**kwargs_for(self.mod, record_response=True))
        self.assertIn("Record", c.calls.create.call_args.kwargs["url"])
        self.assertEqual(c.calls.create.call_args.kwargs["record"], "false")

    def test_twilio_error_returned(self):
        c = self.client()
        c.calls.create.side_effect = twilio_error("boom")
        r = self.mod.call_forward_switch(**kwargs_for(self.mod))
        self.assertIsNone(r["sid"])
        self.assertIsInstance(r["error"], TwilioRestException)


class StatusTests(_Base):
    def test_check_call_finished(self):
        c = self.client()
        for status, finished in [("queued", False), ("ringing", False),
                                 ("in-progress", False), ("completed", True),
                                 ("failed", True), ("busy", True)]:
            with self.subTest(status=status):
                c.calls.return_value.fetch.return_value = types.SimpleNamespace(status=status)
                r = self.mod.outbound_check_call_finished("sid", "tok", "CA1")
                self.assertEqual(r["finished"], finished)

    def test_check_call_finished_error_and_validation(self):
        c = self.client()
        c.calls.return_value.fetch.side_effect = twilio_error("x")
        r = self.mod.outbound_check_call_finished("sid", "tok", "CA1")
        self.assertTrue(r["finished"])
        self.assertIsNotNone(r["error"])
        with self.assertRaises(ValueError):
            self.mod.outbound_check_call_finished("sid", "tok", "")

    def test_calls_and_recordings_finished(self):
        c = self.client()
        c.calls.return_value.fetch.return_value = types.SimpleNamespace(status="in-progress")
        r = self.mod.outbound_check_call_and_recordings_finished("sid", "tok", "CA1")
        self.assertFalse(r["finished"])

        c.calls.return_value.fetch.return_value = types.SimpleNamespace(status="completed")
        c.recordings.list.return_value = [
            types.SimpleNamespace(status="completed"), types.SimpleNamespace(status="processing")]
        r = self.mod.outbound_check_call_and_recordings_finished("sid", "tok", "CA1")
        self.assertFalse(r["finished"])
        self.assertEqual(r["recording_status"], "processing")

        c.recordings.list.return_value = [types.SimpleNamespace(status="completed")]
        r = self.mod.outbound_check_call_and_recordings_finished("sid", "tok", "CA1")
        self.assertTrue(r["finished"])

    def test_calls_and_recordings_errors(self):
        c = self.client()
        c.calls.return_value.fetch.side_effect = twilio_error("x")
        self.assertIsNotNone(
            self.mod.outbound_check_call_and_recordings_finished("sid", "tok", "CA1")["error"])
        c.calls.return_value.fetch.side_effect = None
        c.calls.return_value.fetch.return_value = types.SimpleNamespace(status="completed")
        c.recordings.list.side_effect = twilio_error("y")
        self.assertIsNotNone(
            self.mod.outbound_check_call_and_recordings_finished("sid", "tok", "CA1")["error"])


class RetrieveRecordingsTests(_Base):
    # (確認録音の秒数, 完了録音の秒数)
    durations = None

    def test_classify_by_duration(self):
        c = self.client()
        confirm_d, done_d = self.durations
        c.recordings.list.return_value = [rec("RE_confirm", confirm_d), rec("RE_done", done_d)]
        r = self.mod.outbound_retreive_recordings("sid", "tok", "CA1")
        self.assertEqual(r["recording_number_confirm_sid"], "RE_confirm")
        self.assertEqual(r["recording_switch_done_sid"], "RE_done")

    def test_no_match(self):
        c = self.client()
        c.recordings.list.return_value = [rec("RE_x", 500)]
        r = self.mod.outbound_retreive_recordings("sid", "tok", "CA1")
        self.assertIsNone(r["recording_number_confirm_sid"])
        self.assertIsNone(r["recording_switch_done_sid"])

    def test_error(self):
        c = self.client()
        c.recordings.list.side_effect = twilio_error("x")
        self.assertIsNotNone(self.mod.outbound_retreive_recordings("sid", "tok", "CA1")["error"])


def _speech(*transcripts):
    return json.dumps({"results": [{"alternatives": [{"transcript": t} for t in transcripts]}]}).encode()


class _Resp:
    def __init__(self, data):
        self._d = data

    def read(self):
        return self._d


class SpeechCheckTests(_Base):
    def http_error(self, code):
        e = self.mod.urllib.error.HTTPError("u", code, "x", {}, None)
        self.addCleanup(e.close)
        return e

    def _patch_net(self, wav=b"RIFF", speech=b""):
        opener = mock.MagicMock()
        opener.open.return_value = _Resp(wav)
        p1 = mock.patch.object(self.mod.urllib.request, "build_opener", return_value=opener)
        p2 = mock.patch.object(self.mod.urllib.request, "urlopen", return_value=_Resp(speech))
        p1.start(); self.addCleanup(p1.stop)
        self.urlopen = p2.start(); self.addCleanup(p2.stop)
        return opener

    def test_number_confirm_ok_by_number(self):
        self._patch_net(speech=_speech("転送先0 3 1 2 3 4 5 6 7 8です"))
        r = self.mod.check_recording_number_confirm("sid", "tok", "RE1", "key", TO)
        self.assertTrue(r["check"])

    def test_number_confirm_ok_by_keyword(self):
        self._patch_net(speech=_speech("だめ", "転送先に登録します"))
        self.assertTrue(self.mod.check_recording_number_confirm("sid", "tok", "RE1", "key", TO)["check"])

    def test_number_confirm_ng(self):
        self._patch_net(speech=_speech("登録番号が誤っています"))
        r = self.mod.check_recording_number_confirm("sid", "tok", "RE1", "key", TO)
        self.assertFalse(r["check"])
        self.assertIsNone(r["error"])

    def test_number_confirm_sends_audio_to_google(self):
        self._patch_net(wav=b"abc", speech=_speech("登録します"))
        self.mod.check_recording_number_confirm("sid", "tok", "RE1", "KEY", TO)
        req = self.urlopen.call_args.args[0]
        self.assertIn("speech.googleapis.com", req.full_url)
        self.assertIn("key=KEY", req.full_url)
        body = json.loads(req.data.decode())
        self.assertEqual(body["config"]["languageCode"], "ja-JP")
        self.assertTrue(body["audio"]["content"])

    def test_number_confirm_http_error_on_download(self):
        opener = self._patch_net()
        opener.open.side_effect = self.http_error(404)
        r = self.mod.check_recording_number_confirm("sid", "tok", "RE1", "key", TO)
        self.assertFalse(r["check"])
        self.assertIsNotNone(r["error"])

    def test_number_confirm_validation(self):
        for args in [("", "tok", "RE1", "key", TO), ("sid", "tok", "", "key", TO),
                     ("sid", "tok", "RE1", "", TO), ("sid", "tok", "RE1", "key", ""),
                     ("sid", "tok", "RE1", "key", "123")]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.mod.check_recording_number_confirm(*args)

    def test_switch_done(self):
        self._patch_net(speech=_speech("設定いたしました"))
        self.assertTrue(self.mod.check_recording_switch_done("sid", "tok", "RE2", "key")["check"])
        self._patch_net(speech=_speech("エラーです"))
        r = self.mod.check_recording_switch_done("sid", "tok", "RE2", "key")
        self.assertFalse(r["check"])

    def test_switch_done_http_errors(self):
        opener = self._patch_net()
        opener.open.side_effect = self.http_error(401)
        self.assertIsNotNone(self.mod.check_recording_switch_done("sid", "tok", "RE2", "key")["error"])
        opener = self._patch_net()
        self.urlopen.side_effect = self.http_error(500)
        r = self.mod.check_recording_switch_done("sid", "tok", "RE2", "key")
        self.assertFalse(r["check"])
        self.assertIsNotNone(r["error"])


class BatchTests(_Base):
    def setUp(self):
        self.msgs = []
        self.v = lambda message: self.msgs.append(message)
        for name in ("time",):
            p = mock.patch.object(self.mod.time, "sleep")
            p.start(); self.addCleanup(p.stop)

    def run_batch(self, **over):
        kw = kwargs_for(self.mod, google_api_key="key", verbose_message_lambda=self.v,
                        wait_limit_sec=10, wait_sleep=5)
        kw.update(over)
        return self.mod.call_forward_switch_batch(**kw)

    def patch(self, name, **kw):
        p = mock.patch.object(self.mod, name, **kw)
        m = p.start(); self.addCleanup(p.stop)
        return m

    def test_validation(self):
        with self.assertRaises(ValueError):
            self.run_batch(google_api_key="")
        with self.assertRaises(ValueError):
            self.run_batch(forward_to_phone_number="1")

    def test_call_error(self):
        self.patch("call_forward_switch", return_value={"sid": None, "call": None, "error": Exception("e")})
        r = self.run_batch()
        self.assertIsNotNone(r["error"])

    def test_success_without_record_response(self):
        self.patch("call_forward_switch", return_value={"sid": "CA1", "call": None, "error": None})
        self.patch("outbound_check_call_and_recordings_finished", return_value={
            "finished": True, "call_status": "completed", "recording_status": None, "error": None})
        self.patch("outbound_retreive_recordings", return_value={
            "recording_number_confirm_sid": None, "recording_switch_done_sid": None,
            "recordings": [], "error": None})
        r = self.run_batch()
        self.assertIsNone(r["error"])
        self.assertEqual(r["call_sid"], "CA1")
        self.assertIn(TO, r["message"])

    def test_timeout(self):
        self.patch("call_forward_switch", return_value={"sid": "CA1", "call": None, "error": None})
        self.patch("outbound_check_call_and_recordings_finished", return_value={
            "finished": False, "call_status": "in-progress", "recording_status": None, "error": None})
        r = self.run_batch()
        self.assertIn("timed out", r["message"])

    def test_status_error(self):
        self.patch("call_forward_switch", return_value={"sid": "CA1", "call": None, "error": None})
        self.patch("outbound_check_call_and_recordings_finished", return_value={
            "finished": None, "call_status": None, "recording_status": None, "error": Exception("s")})
        self.assertEqual(self.run_batch()["message"], "s")

    def _record_response_setup(self, confirm, done):
        self.patch("call_forward_switch", return_value={"sid": "CA1", "call": None, "error": None})
        self.patch("outbound_check_call_and_recordings_finished", return_value={
            "finished": True, "call_status": "completed", "recording_status": "completed", "error": None})
        self.patch("outbound_retreive_recordings", return_value={
            "recording_number_confirm_sid": "R1", "recording_switch_done_sid": "R2",
            "recordings": [], "error": None})
        self.patch("check_recording_number_confirm", return_value=confirm)
        self.patch("check_recording_switch_done", return_value=done)

    def test_record_response_success(self):
        ok = {"check": True, "transcript": "t", "error": None}
        self._record_response_setup(ok, ok)
        r = self.run_batch(record_response=True)
        self.assertIsNone(r["error"])
        self.assertEqual(r["recording_number_confirm_sid"], "R1")
        self.assertEqual(r["recording_switch_done_sid"], "R2")

    def test_record_response_number_confirm_ng(self):
        self._record_response_setup({"check": False, "transcript": "t", "error": None},
                                    {"check": True, "transcript": "t", "error": None})
        self.assertIn("Number confirm", self.run_batch(record_response=True)["message"])

    def test_record_response_switch_done_ng(self):
        self._record_response_setup({"check": True, "transcript": "t", "error": None},
                                    {"check": False, "transcript": "t", "error": None})
        self.assertIn("Switch done", self.run_batch(record_response=True)["message"])

    def test_record_response_switch_done_error(self):
        err = Exception("net")
        self._record_response_setup({"check": True, "transcript": "t", "error": None},
                                    {"check": False, "transcript": None, "error": err})
        self.assertIs(self.run_batch(record_response=True)["error"], err)



def _make(base_cls, mod, **attrs):
    return type(base_cls.__name__ + "_" + mod.__name__.rsplit(".", 1)[1].upper(),
                (base_cls, unittest.TestCase), dict(mod=mod, **attrs))


for _m, _dur in ((dcm, (15, 5)),):
    for _c in (CallForwardSwitchTests, StatusTests, SpeechCheckTests, BatchTests):
        globals()[_make(_c, _m).__name__] = _make(_c, _m)
    _r = _make(RetrieveRecordingsTests, _m, durations=_dur)
    globals()[_r.__name__] = _r

# 基底クラスはunittest.TestCaseではないのでdiscoverの対象外。


class TopLevelDispatchTests(unittest.TestCase):
    def kw(self):
        return dict(
            career="dcm", twilio_sid="s", twilio_token="t", twilio_phone_number="+81",
            transfer_service_career_phone_number="+81570", forward_from_phone_number=FROM,
            forward_from_network_pass=PASS, forward_to_phone_number=TO,
            record_entire=False, record_response=False, google_api_key="k")

    def test_dispatch(self):
        for career, mod in (("dcm", dcm),):
            with self.subTest(career=career), \
                    mock.patch.object(mod, "call_forward_switch_batch", return_value="ok") as m:
                kw = self.kw(); kw["career"] = career
                self.assertEqual(top.call_forward_switch_batch(**kw), "ok")
                key = "transfer_service_%s_phone_number" % career
                self.assertEqual(m.call_args.kwargs[key], "+81570")

    def test_invalid_career(self):
        kw = self.kw(); kw["career"] = "xxx"
        with self.assertRaises(ValueError):
            top.call_forward_switch_batch(**kw)


class XmlShortenTests(unittest.TestCase):
    def test_shorten(self):
        self.assertEqual(dcm._xml_shorten("\n   <a>\n      <b/>\n   </a>\n"), "<a><b/></a>")


if __name__ == "__main__":
    unittest.main()

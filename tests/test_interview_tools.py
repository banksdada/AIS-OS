import importlib.util
import io
import os
import re
import subprocess  # noqa: F401  (real module kept for other tests; fakes are per-test)
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _load(modname, relpath):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(ROOT, relpath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


spk = _load('spk', 'scripts/speak.py')
itx = _load('itx', 'scripts/interview-transcribe.py')


class FakeSay:
    def __init__(self, stdout_text='Daniel en_GB # hi'):
        self.calls = []
        self.stdout_text = stdout_text

    def run(self, cmd, *a, **k):
        self.calls.append(list(cmd))
        return types.SimpleNamespace(stdout=self.stdout_text, returncode=0)


class SpeakRules(unittest.TestCase):
    def _main(self, argv, fake, which='say'):
        with patch.object(spk, 'subprocess', fake), \
                patch.object(spk, 'shutil', types.SimpleNamespace(which=lambda p: which)), \
                patch.object(sys, 'argv', ['speak.py'] + argv):
            try:
                spk.main()
            except SystemExit as e:
                if e.code not in (0, None):
                    raise
            return fake

    def test_1_missing_say_skips_gracefully(self):
        fake = FakeSay()
        with patch.object(spk, 'subprocess', fake), \
                patch.object(spk, 'shutil', types.SimpleNamespace(which=lambda p: None)), \
                patch.object(sys, 'argv', ['speak.py', 'hello']):
            spk.main()
        self.assertEqual(fake.calls, [])

    def test_2_voices_lists_without_speaking(self):
        fake = FakeSay()
        self._main(['--voices'], fake)
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(fake.calls[0][:3], ['say', '-v', '?'])

    def test_3_file_source_beats_positional(self):
        fd, path = tempfile.mkstemp(suffix='.txt')
        os.write(fd, b'FileText'); os.close(fd)
        fake = FakeSay()
        self._main(['--file', path, 'PosArg'], fake)
        os.unlink(path)
        self.assertEqual(fake.calls[-1][-1], 'FileText')

    def test_4_no_text_source_errors_without_speaking(self):
        fake = FakeSay()
        with patch.object(spk, 'subprocess', fake), \
                patch.object(sys, 'argv', ['speak.py']):
            with self.assertRaises(SystemExit) as ctx:
                spk.main()
        self.assertEqual(ctx.exception.code, 2)
        self.assertEqual(fake.calls, [])

    def test_5_default_voice_is_daniel(self):
        fake = FakeSay()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('AIOS_VOICE', None)
            self._main(['hi'], fake)
        cmd = fake.calls[-1]
        self.assertEqual(cmd[cmd.index('-v') + 1], 'Daniel')

    def test_6_env_voice_overrides_default(self):
        fake = FakeSay()
        with patch.dict(os.environ, {'AIOS_VOICE': 'Karen'}):
            self._main(['hi'], fake)
        cmd = fake.calls[-1]
        self.assertEqual(cmd[cmd.index('-v') + 1], 'Karen')

    def test_7_flag_beats_env(self):
        fake = FakeSay()
        with patch.dict(os.environ, {'AIOS_VOICE': 'Karen'}):
            self._main(['--voice', 'Fred', 'hi'], fake)
        cmd = fake.calls[-1]
        self.assertEqual(cmd[cmd.index('-v') + 1], 'Fred')

    def test_8_default_rate_190_and_flag_override(self):
        fake = FakeSay()
        self._main(['hi'], fake)
        self.assertEqual(fake.calls[-1][fake.calls[-1].index('-r') + 1], '190')
        self._main(['--rate', '120', 'hi'], fake)
        self.assertEqual(fake.calls[-1][fake.calls[-1].index('-r') + 1], '120')

    def test_9_whitespace_collapsed_before_speech(self):
        fake = FakeSay()
        self._main(['a\n  b\t\nc'], fake)
        self.assertEqual(fake.calls[-1][-1], 'a b c')


class FakeSD:
    def __init__(self, levels):
        self.levels = list(levels)
        self.recs = []

    def rec(self, n, **kw):
        self.recs.append((n, kw))
        if not self.levels:
            raise KeyboardInterrupt
        level = self.levels.pop(0)
        if level == 'KI':
            raise KeyboardInterrupt
        return np.full((n, 1), level, dtype=np.float32)

    def wait(self):
        pass


class FakeModel:
    def __init__(self, text='Hello world'):
        self.text = text
        self.calls = []

    def transcribe(self, audio, **kw):
        self.calls.append((audio, kw))
        seg = types.SimpleNamespace(start=0.0, end=0.5, text=self.text)
        return ([seg], types.SimpleNamespace())


def _run_itx(argv, model, sd, out):
    with patch.object(itx, 'load_model', lambda name: model), \
            patch.dict(sys.modules, {'sounddevice': sd}), \
            patch.object(sys, 'argv', ['itx.py', '--out', out] + argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            itx.main()
        return buf.getvalue()


class TranscribeRules(unittest.TestCase):
    def setUp(self):
        self.fd, self.out = tempfile.mkstemp(suffix='.txt')
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.out)

    def test_sr_constant_is_16khz(self):
        self.assertEqual(itx.SR, 16000)

    def test_model_choices_reject_unknown(self):
        model = FakeModel()
        sd = FakeSD(['KI'])
        with patch.object(itx, 'load_model', lambda name: model), \
                patch.object(sys, 'argv', ['itx.py', '--model', 'medium']):
            with self.assertRaises(SystemExit):
                itx.main()
        self.assertEqual(model.calls, [])

    def test_silence_is_never_transcribed(self):
        model = FakeModel()
        sd = FakeSD([1e-5, 'KI'])
        _run_itx(['--chunk', '0.01'], model, sd, self.out)
        self.assertEqual(model.calls, [])

    def test_speech_emits_timestamped_line_to_stdout_and_file(self):
        model = FakeModel('Good afternoon')
        sd = FakeSD([0.01, 'KI'])
        out_buf = _run_itx(['--chunk', '0.01'], model, sd, self.out)
        line_re = re.compile(r'^\[\d{2}:\d{2}:\d{2}\] Good afternoon$', re.M)
        self.assertRegex(out_buf, line_re)
        self.assertRegex(open(self.out).read(), line_re)

    def test_duplicate_segment_emitted_once(self):
        model = FakeModel('Same line')
        sd = FakeSD([0.01, 0.01, 'KI'])
        out_buf = _run_itx(['--chunk', '0.01'], model, sd, self.out)
        self.assertEqual(out_buf.count('Same line'), 1)

    def test_rec_uses_16k_mono_float32(self):
        model = FakeModel()
        sd = FakeSD([1e-5, 'KI'])
        _run_itx(['--chunk', '0.01'], model, sd, self.out)
        n, kw = sd.recs[0]
        self.assertEqual(kw['samplerate'], 16000)
        self.assertEqual(kw['channels'], 1)
        self.assertEqual(str(kw['dtype']), 'float32')

    def test_ctrl_c_stops_cleanly(self):
        model = FakeModel()
        sd = FakeSD([1e-5, 'KI'])
        out_buf = _run_itx(['--chunk', '0.01'], model, sd, self.out)
        self.assertIn('stopped', out_buf)

    def test_context_prompt_reaches_stream_transcribe(self):
        model = FakeModel()
        sd = FakeSD([0.01, 'KI'])
        _run_itx(['--chunk', '0.01'], model, sd, self.out)
        audio, kw = model.calls[0]
        self.assertIn('Banks Dada', kw.get('initial_prompt', ''))

    def test_file_mode_ffmpeg_mono_pcm_and_prompt(self):
        model = FakeModel('From file')
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(list(cmd))
            return types.SimpleNamespace(stdout=b'\x01\x00\x02\x00\x03\x00\x04\x00')

        fake_sub = types.SimpleNamespace(run=fake_run)
        with patch.object(itx, 'load_model', lambda name: model), \
                patch.dict(sys.modules, {'subprocess': fake_sub}), \
                patch.object(sys, 'argv', ['itx.py', '--file', 'x.wav', '--out', self.out]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                itx.main()
        cmd = calls[0]
        self.assertEqual(cmd[cmd.index('-ac') + 1], '1')
        self.assertEqual(cmd[cmd.index('-ar') + 1], '16000')
        audio, kw = model.calls[0]
        self.assertEqual(len(audio), 4)
        self.assertEqual(str(audio.dtype), 'float32')
        self.assertIn('Banks Dada', kw.get('initial_prompt', ''))
        self.assertIn('From file', buf.getvalue())

    def test_rms_known_values(self):
        self.assertEqual(itx.rms(np.zeros(0, dtype=np.float32)), 0.0)
        self.assertAlmostEqual(itx.rms(np.array([0.5, -0.5], dtype=np.float32)), 0.5, places=6)


if __name__ == '__main__':
    unittest.main()

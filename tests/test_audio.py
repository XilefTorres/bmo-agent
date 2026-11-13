"""Pruebas de la mezcla (no abren ningún dispositivo de audio)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import numpy as np
    from modules import audio
except Exception as e:  # sin numpy/sounddevice/PortAudio no se puede importar el módulo
    audio = None
    _import_error = e


@unittest.skipIf(audio is None, "numpy/sounddevice no disponibles")
class MixTest(unittest.TestCase):
    def test_two_sounds_are_summed(self):
        a = audio.Sound(np.full(10, 0.25, dtype=np.float32), "voice")
        b = audio.Sound(np.full(4, 0.5, dtype=np.float32), "metronome")
        out = np.zeros(8, dtype=np.float32)
        finished = audio.mix_into(out, [a, b])
        np.testing.assert_allclose(out[:4], 0.75)
        np.testing.assert_allclose(out[4:], 0.25)
        self.assertEqual(finished, [b])     # el corto terminó, la voz sigue
        self.assertEqual(a.pos, 8)

    def test_mix_is_clipped(self):
        a = audio.Sound(np.full(4, 0.9, dtype=np.float32), "voice")
        b = audio.Sound(np.full(4, 0.9, dtype=np.float32), "fx")
        out = np.zeros(4, dtype=np.float32)
        audio.mix_into(out, [a, b])
        np.testing.assert_allclose(out, 1.0)

    def test_resample_doubles_length(self):
        src = np.linspace(-1, 1, 100, dtype=np.float32)
        out = audio.resample(src, audio.SAMPLE_RATE // 2)
        self.assertEqual(len(out), 200)
        self.assertAlmostEqual(float(out[0]), -1.0, places=5)
        self.assertAlmostEqual(float(out[-1]), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()

"""Pruebas sin hardware. Ejecutar desde la raíz del proyecto:  python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.text_utils import (  # noqa: E402
    contains_phrase, remove_phrases, parse_duration, format_duration, parse_price, trim_to_sentence,
    pop_sentences, in_time_range, parse_clock_time, format_clock,
)
from datetime import datetime  # noqa: E402


class RouterTest(unittest.TestCase):
    def test_keyword_is_whole_word(self):
        self.assertFalse(contains_phrase("qué tipo de música te gusta", ["ip"]))
        self.assertFalse(contains_phrase("con mi equipo desde el principio", ["ip"]))
        self.assertTrue(contains_phrase("cuál es tu ip", ["ip"]))
        self.assertFalse(contains_phrase("qué hago ahora", ["qué hora", "la hora"]))
        self.assertTrue(contains_phrase("oye qué hora es", ["qué hora", "la hora"]))

    def test_accents_are_ignored(self):
        self.assertTrue(contains_phrase("apágate", ["apagate"]))
        self.assertTrue(contains_phrase("pon el metronomo", ["metrónomo"]))

    def test_wake_words(self):
        wake = ["bmo", "beemo", "vimos"]
        self.assertFalse(contains_phrase("mi primo está vivo", wake))
        self.assertTrue(contains_phrase("BMO qué hora es", wake))
        self.assertEqual(remove_phrases("bmo cuéntame de méxico", wake), "cuéntame de méxico")

    def test_remove_keeps_accents(self):
        self.assertEqual(remove_phrases("cuanto cuesta una cámara", ["cuánto cuesta"]), "una cámara")


class DurationTest(unittest.TestCase):
    def seconds(self, text):
        parsed = parse_duration(text)
        return parsed[0] if parsed else None

    def test_digits(self):
        self.assertEqual(self.seconds("alarma en 5 minutos"), 300)
        self.assertEqual(self.seconds("alarma en 1 hora y 30 minutos"), 5400)

    def test_words(self):
        self.assertEqual(self.seconds("despiértame en una hora"), 3600)
        self.assertEqual(self.seconds("despiértame en media hora"), 1800)
        self.assertEqual(self.seconds("alarma en cinco minutos"), 300)
        self.assertEqual(self.seconds("alarma en una hora y media"), 5400)
        self.assertEqual(self.seconds("alarma en cuarenta y cinco segundos"), 45)
        self.assertEqual(self.seconds("alarma en veintidós minutos"), 22 * 60)

    def test_no_duration(self):
        self.assertIsNone(self.seconds("ponme una alarma"))
        self.assertIsNone(self.seconds("qué tiempo hace"))

    def test_span_points_at_original_text(self):
        text = "recuérdame sacar la basura en 5 minutos"
        _, start, end = parse_duration(text)
        self.assertEqual(text[start:end], "5 minutos")

    def test_format(self):
        self.assertEqual(format_duration(60), "1 minuto")
        self.assertEqual(format_duration(300), "5 minutos")
        self.assertEqual(format_duration(5400), "1 hora y 30 minutos")
        self.assertEqual(format_duration(3661), "1 hora, 1 minuto y 1 segundo")


class ClockTest(unittest.TestCase):
    def due(self, text, now):
        parsed = parse_clock_time(text, now)
        return parsed[0] if parsed else None

    def test_explicit_period(self):
        now = datetime(2026, 11, 13, 15, 0)   # viernes, 3 de la tarde
        self.assertEqual(self.due("alarma a las 9 de la mañana", now), datetime(2026, 11, 14, 9, 0))
        self.assertEqual(self.due("alarma a las 7 de la tarde", now), datetime(2026, 11, 13, 19, 0))
        self.assertEqual(self.due("alarma a las 10 de la noche", now), datetime(2026, 11, 13, 22, 0))
        self.assertEqual(self.due("alarma a las 12 de la noche", now), datetime(2026, 11, 14, 0, 0))
        self.assertEqual(self.due("alarma a las 6 p.m.", now), datetime(2026, 11, 13, 18, 0))
        self.assertEqual(self.due("alarma a las 6:30 a. m.", now), datetime(2026, 11, 14, 6, 30))

    def test_ambiguous_hour_takes_next_occurrence(self):
        self.assertEqual(self.due("alarma a las 11", datetime(2026, 11, 13, 15, 0)), datetime(2026, 11, 13, 23, 0))
        self.assertEqual(self.due("alarma a las 11", datetime(2026, 11, 13, 8, 0)), datetime(2026, 11, 13, 11, 0))
        self.assertEqual(self.due("alarma a las 11", datetime(2026, 11, 13, 23, 30)), datetime(2026, 11, 14, 11, 0))
        self.assertEqual(self.due("alarma a las 18", datetime(2026, 11, 13, 15, 0)), datetime(2026, 11, 13, 18, 0))

    def test_minutes_and_words(self):
        now = datetime(2026, 11, 13, 15, 0)
        self.assertEqual(self.due("despiértame a las siete y media de la mañana", now), datetime(2026, 11, 14, 7, 30))
        self.assertEqual(self.due("alarma a las 9:15 de la noche", now), datetime(2026, 11, 13, 21, 15))
        self.assertEqual(self.due("alarma a la una y cuarto de la tarde", now), datetime(2026, 11, 14, 13, 15))
        self.assertEqual(self.due("avísame al mediodía", now), datetime(2026, 11, 14, 12, 0))

    def test_tomorrow(self):
        now = datetime(2026, 11, 13, 7, 0)
        self.assertEqual(self.due("alarma mañana a las 9", now), datetime(2026, 11, 14, 9, 0))
        self.assertEqual(self.due("alarma a las 9 de la mañana", now), datetime(2026, 11, 13, 9, 0))

    def test_no_clock(self):
        now = datetime(2026, 11, 13, 15, 0)
        self.assertIsNone(self.due("ponme una alarma", now))
        self.assertIsNone(self.due("alarma en 5 minutos", now))

    def test_format(self):
        self.assertEqual(format_clock(datetime(2026, 1, 1, 9, 0)), "las 9 de la mañana")
        self.assertEqual(format_clock(datetime(2026, 1, 1, 13, 30)), "la 1 y 30 de la tarde")
        self.assertEqual(format_clock(datetime(2026, 1, 1, 23, 0)), "las 11 de la noche")
        self.assertEqual(format_clock(datetime(2026, 1, 1, 0, 0)), "las 12 de la mañana")


class MiscTest(unittest.TestCase):
    def test_price(self):
        self.assertEqual(parse_price("1,299"), 1299.0)
        self.assertEqual(parse_price("$ 12,499.50"), 12499.5)
        self.assertIsNone(parse_price("Agotado"))

    def test_pop_sentences(self):
        # La oración corta se junta con la siguiente; lo incompleto se queda en el buffer
        sentences, rest = pop_sentences("¡Hola! Soy BMO, tu amigo robot. Me gusta ju")
        self.assertEqual(sentences, ["¡Hola! Soy BMO, tu amigo robot."])
        self.assertEqual(rest, "Me gusta ju")
        self.assertEqual(pop_sentences("Sin terminar todavía"), ([], "Sin terminar todavía"))

    def test_quiet_hours_cross_midnight(self):
        from datetime import time
        start, end = time(22, 0), time(8, 0)
        self.assertTrue(in_time_range(time(22, 30), start, end))
        self.assertTrue(in_time_range(time(3, 0), start, end))
        self.assertFalse(in_time_range(time(8, 0), start, end))
        self.assertFalse(in_time_range(time(20, 30), start, end))
        self.assertTrue(in_time_range(time(13, 0), time(12, 0), time(14, 0)))

    def test_trim(self):
        self.assertEqual(trim_to_sentence("¡Hola! Soy BMO. Me gusta ju"), "¡Hola! Soy BMO.")
        self.assertEqual(trim_to_sentence("Todo completo."), "Todo completo.")
        self.assertEqual(trim_to_sentence("sin puntuación"), "sin puntuación")


if __name__ == "__main__":
    unittest.main()

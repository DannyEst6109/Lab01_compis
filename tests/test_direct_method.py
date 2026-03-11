import unittest

from main import compile_regex
from src.simulator import simulate_dfa


class DirectMethodTests(unittest.TestCase):
    def assertAccepts(self, regex: str, accepted: str, rejected: str):
        compiled = compile_regex(regex)
        ok, _ = simulate_dfa(compiled["transitions"], compiled["accepting_states"], accepted)
        bad, _ = simulate_dfa(
            compiled["transitions"], compiled["accepting_states"], rejected
        )
        self.assertTrue(ok, f"La cadena '{accepted}' debe ser aceptada por {regex}")
        self.assertFalse(bad, f"La cadena '{rejected}' debe ser rechazada por {regex}")

    def test_kleene_and_union(self):
        self.assertAccepts("a(b|c)*", "abcb", "acbd")

    def test_positive_and_optional(self):
        self.assertAccepts("(ab)+c?", "ababc", "ac")

    def test_optional_union_positive(self):
        self.assertAccepts("(a|b)?c+", "bcc", "ab")


if __name__ == "__main__":
    unittest.main()

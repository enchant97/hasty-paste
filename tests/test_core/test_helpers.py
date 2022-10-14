import re
from datetime import datetime, timedelta
from unittest import TestCase

from paste_bin import config
from paste_bin.core import helpers


class TestGenId(TestCase):
    def test_valid(self):
        self.assertEqual(len(helpers.gen_id(0)), 0)
        self.assertEqual(len(helpers.gen_id(5)), 5)
        self.assertEqual(len(helpers.gen_id(100)), 100)


class TestCreatePasteId(TestCase):
    def test_valid_short(self):
        self.assertEqual(len(helpers.create_paste_id()), helpers.PASTE_ID_SHORT_LEN)

    def test_valid_long(self):
        self.assertEqual(len(helpers.create_paste_id(True)), helpers.PASTE_ID_LONG_LEN)

    def test_valid_characters(self):
        self.assertTrue(re.match(
            helpers.VALID_PASTE_ID_REGEX,
            helpers.create_paste_id(False)
        ))


class TestMakeDefaultExpiresAt(TestCase):
    def test_disabled(self):
        conf = config.ExpireTimeDefaultSettings(
            ENABLE=False,
        )
        result = helpers.make_default_expires_at(conf)
        self.assertIsNone(result)

    def test_enabled(self):
        conf = config.ExpireTimeDefaultSettings(
            ENABLE=True,
            MINUTES=0,
            HOURS=0,
            DAYS=1,
        )
        expected = datetime.utcnow() + timedelta(days=1)
        result = helpers.make_default_expires_at(conf)
        self.assertIsNotNone(result)
        self.assertEqual(
            expected.isoformat(timespec="hours"),
            result.isoformat(timespec="hours"),  # type: ignore
        )


class TestPaddStr(TestCase):
    def _make_pad_test(self, expected: str, sep: str, everyN: int):
        to_test = expected.replace(sep, "")
        actual = helpers.padd_str(to_test, sep, everyN)
        self.assertEqual(expected, actual)

    def test_shorter(self):
        self._make_pad_test("8Z2", "-", 5)

    def test_equal(self):
        self._make_pad_test("8Z2ka", "-", 5)

    def test_one_pad(self):
        self._make_pad_test("8Z2kX-cZioc", "-", 5)
        self._make_pad_test("8Z2kX--cZioc", "--", 5)

    def test_not_matching(self):
        self._make_pad_test("8Z2kX-cZioca", "-", 5)
        self._make_pad_test("8Z2-kXc-Zioca", "-", 3)
        self._make_pad_test("8Z2kX--cZioca", "--", 5)

    def test_longer(self):
        self._make_pad_test("8Z2kX-cZioc-a3gAs", "-", 5)
        self._make_pad_test("8Z2kX--cZioc--a3gAs", "--", 5)

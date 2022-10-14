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
        self.assertEqual(len(helpers.create_paste_id()), 10)

    def test_valid_long(self):
        self.assertEqual(len(helpers.create_paste_id(True)), 40)


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

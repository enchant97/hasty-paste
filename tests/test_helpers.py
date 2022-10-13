from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase

from paste_bin import config, helpers

VALID_PASTE_META = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
                   b'"2022-07-26T18:55:17.497161", "expire_dt": null}'
VALID_DT_ISO_STRING = "2022-07-26T18:55:17.497161"


class TestExtractPasteMeta(TestCase):
    def test_valid(self):
        self.assertIsInstance(
            helpers.extract_paste_meta(VALID_PASTE_META),
            helpers.PasteMeta,
        )

    def test_invalid_version(self):
        test_data = '{"version": 0}'
        self.assertRaises(helpers.PasteMetaVersionInvalid, helpers.extract_paste_meta, test_data)

    def test_invalid_meta(self):
        test_data = "{version: "
        self.assertRaises(helpers.PasteMetaUnprocessable, helpers.extract_paste_meta, test_data)

    def test_is_expired(self):
        now = datetime.utcnow()
        before = now - timedelta(weeks=1)
        after = now + timedelta(weeks=1)
        meta = helpers.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
            expire_dt=after,
        )
        self.assertFalse(meta.is_expired)
        meta_no_expiry = helpers.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
        )
        self.assertFalse(meta_no_expiry.is_expired)
        meta_expired = helpers.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
            expire_dt=before,
        )
        self.assertTrue(meta_expired.is_expired)


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


class TestGetIdFromPastePath(TestCase):
    def test_valid(self):
        part_1 = "12"
        part_2 = "agfew"
        expected_output = part_1 + part_2
        root = Path("pastes/")
        test_input = root / part_1 / part_2

        actual_output = helpers.get_id_from_paste_path(root, test_input)

        self.assertEqual(expected_output, actual_output)


class TestGetFormDatetime(TestCase):
    def test_valid_dt(self):
        self.assertIsInstance(helpers.get_form_datetime(VALID_DT_ISO_STRING), datetime)

    def test_valid_none(self):
        self.assertIsNone(helpers.get_form_datetime(None))

    def test_invalid(self):
        self.assertRaises(ValueError, helpers.get_form_datetime, "202A-07-26")


class TestIsValidLexerName(TestCase):
    def test_true(self):
        self.assertTrue(helpers.is_valid_lexer_name("python"))

    def test_false(self):
        self.assertFalse(helpers.is_valid_lexer_name("testing123"))


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
        expected = datetime.now() + timedelta(days=1)
        result = helpers.make_default_expires_at(conf)
        self.assertIsNotNone(result)
        self.assertEqual(
            expected.isoformat(timespec="hours"),
            result.isoformat(timespec="hours"),  # type: ignore
        )

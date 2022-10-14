from datetime import datetime, timedelta
from unittest import TestCase

from paste_bin import config, helpers

VALID_PASTE_META = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
                   b'"2022-07-26T18:55:17.497161", "expire_dt": null}'


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

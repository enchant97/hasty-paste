from datetime import datetime, timedelta
from unittest import TestCase

from paste_bin.core import models

VALID_PASTE_META__NO_EXPIRE = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
    b'"2022-07-26T18:55:17.497161", "expire_dt": null}'


class TestPasteMeta(TestCase):
    def test_extract_from_line__valid(self):
        self.assertIsInstance(
            models.PasteMeta.extract_from_line(VALID_PASTE_META__NO_EXPIRE),
            models.PasteMeta,
        )

    def test_extract_from_line__invalid_version(self):
        test_data = '{"version": 0}'
        self.assertRaises(
            models.PasteMetaVersionInvalid,
            models.PasteMeta.extract_from_line, test_data
        )

    def test_extract_from_line__invalid_meta(self):
        test_data = "{version: "
        self.assertRaises(
            models.PasteMetaUnprocessable,
            models.PasteMeta.extract_from_line, test_data
        )

    def test_is_expired__valid(self):
        now = datetime.utcnow()
        before = now - timedelta(weeks=1)
        after = now + timedelta(weeks=1)
        meta = models.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
            expire_dt=after,
        )
        self.assertFalse(meta.is_expired)
        meta_no_expiry = models.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
        )
        self.assertFalse(meta_no_expiry.is_expired)
        meta_expired = models.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
            expire_dt=before,
        )
        self.assertTrue(meta_expired.is_expired)

    def test_until_expiry__no_expire(self):
        now = datetime.utcnow()
        meta = models.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
        )
        self.assertIsNone(meta.until_expiry())

    def test_until_expiry__with_expire(self):
        now = datetime.utcnow()
        expire_delta = timedelta(days=4)
        expire_dt = now + expire_delta
        meta = models.PasteMeta(
            paste_id="te1200aa",
            creation_dt=now,
            expire_dt=expire_dt,
        )
        result = meta.until_expiry().total_seconds()
        expected = expire_delta.total_seconds()

        # check that it is roughly correct (+- 4 seconds)
        self.assertGreaterEqual(expected, result)
        self.assertLess(expected, result + 4)


class PasteMetaToCreate(TestCase):
    def test_into_meta__valid(self):
        to_create = models.PasteMetaToCreate()
        result = to_create.into_meta(paste_id="abc")
        self.assertEqual(type(result), models.PasteMeta)
        self.assertEqual(result.paste_id, "abc")


class TestPasteApiCreate(TestCase):
    def test_title_validator__valid(self):
        models.PasteApiCreate(
            content="",
            paste_id="te1200aa",
            creation_dt=datetime.utcnow(),
            title="hello",
        )

    def test_title_validator__invalid(self):
        with self.assertRaises(ValueError):
            meta = models.PasteApiCreate(
                content="",
                paste_id="te1200aa",
                creation_dt=datetime.utcnow(),
                title="a"*40,
            )

    def test_lexer_name_validator__valid(self):
        models.PasteApiCreate(
            content="",
            paste_id="te1200aa",
            creation_dt=datetime.utcnow(),
            lexer_name="py",
        )

    def test_lexer_name_validator__invalid(self):
        with self.assertRaises(ValueError):
            models.PasteApiCreate(
                content="",
                paste_id="te1200aa",
                creation_dt=datetime.utcnow(),
                lexer_name="-",
            )

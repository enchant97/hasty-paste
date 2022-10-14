from datetime import datetime, timedelta
from unittest import TestCase

from paste_bin.core import models

VALID_PASTE_META = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
                   b'"2022-07-26T18:55:17.497161", "expire_dt": null}'


class TestExtractPasteMeta(TestCase):
    def test_valid(self):
        self.assertIsInstance(
            models.PasteMeta.extract_from_line(VALID_PASTE_META),
            models.PasteMeta,
        )

    def test_invalid_version(self):
        test_data = '{"version": 0}'
        self.assertRaises(
            models.PasteMetaVersionInvalid,
            models.PasteMeta.extract_from_line, test_data
        )

    def test_invalid_meta(self):
        test_data = "{version: "
        self.assertRaises(
            models.PasteMetaUnprocessable,
            models.PasteMeta.extract_from_line, test_data
        )

    def test_is_expired(self):
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

from datetime import datetime
from unittest import TestCase

from paste_bin import helpers

VALID_PASTE_META = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
                   b'"2022-07-26T18:55:17.497161", "expire_dt": null}'
VALID_DT_ISO_STRING = "2022-07-26T18:55:17.497161"


class TestGetPasteMeta(TestCase):
    def test_valid(self):
        self.assertIsInstance(
            helpers.get_paste_meta(VALID_PASTE_META),
            helpers.PasteMeta
        )


class TestCreatePasteId(TestCase):
    def test_valid_short(self):
        self.assertEqual(len(helpers.create_paste_id()), 16)

    def test_valid_long(self):
        self.assertEqual(len(helpers.create_paste_id(True)), 40)


class TestGetFormDatetime(TestCase):
    def test_valid_dt(self):
        self.assertIsInstance(helpers.get_form_datetime(VALID_DT_ISO_STRING), datetime)

    def test_valid_none(self):
        self.assertIsNone(helpers.get_form_datetime(None))

    def test_invalid(self):
        self.assertRaises(ValueError, helpers.get_form_datetime, "202A-07-26")

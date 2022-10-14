from datetime import datetime
from unittest import TestCase

from paste_bin.core import conversion

VALID_DT_ISO_STRING = "2022-07-26T18:55:17.497161"


class TestGetFormDatetime(TestCase):
    def test_valid_dt(self):
        self.assertIsInstance(conversion.form_field_to_datetime(VALID_DT_ISO_STRING), datetime)

    def test_valid_none(self):
        self.assertIsNone(conversion.form_field_to_datetime(None))

    def test_invalid(self):
        self.assertRaises(ValueError, conversion.form_field_to_datetime, "202A-07-26")

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, TestCase

from paste_bin import helpers

TEST_DATA_PATH = Path("data/tests")
VALID_PASTE_META = b'{"paste_id": "601cdec402c931ad", "creation_dt": ' + \
                   b'"2022-07-26T18:55:17.497161", "expire_dt": null}'
VALID_DT_ISO_STRING = "2022-07-26T18:55:17.497161"
VALID_META_OBJ = helpers.PasteMeta(
    paste_id="te1200aa",
    creation_dt=datetime.utcnow(),
)


class TestGetPasteMeta(TestCase):
    def test_valid(self):
        self.assertIsInstance(
            helpers.get_paste_meta(VALID_PASTE_META),
            helpers.PasteMeta,
        )

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


class TestCreatePasteId(TestCase):
    def test_valid_short(self):
        self.assertEqual(len(helpers.create_paste_id()), 10)

    def test_valid_long(self):
        self.assertEqual(len(helpers.create_paste_id(True)), 40)


class TestCreatePastePath(TestCase):
    def setUp(self):
        TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

    def test_valid(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            paste_id = "1234ABCD"
            expected_result = root.joinpath(paste_id[:2], paste_id[2:])
            self.assertEqual(helpers.create_paste_path(root, paste_id), expected_result)
            self.assertFalse(root.joinpath(paste_id[:2]).is_dir())

    def test_valid_mkdir(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            paste_id = "1234ABCE"
            expected_result = root.joinpath(paste_id[:2], paste_id[2:])
            self.assertEqual(helpers.create_paste_path(root, paste_id, True), expected_result)
            self.assertTrue(root.joinpath(paste_id[:2]).is_dir())

    def test_invalid_id(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            paste_id = "12"
            self.assertRaises(ValueError, helpers.create_paste_path, root, paste_id, False)
            self.assertRaises(ValueError, helpers.create_paste_path, root, paste_id, True)


class TestWritePaste(IsolatedAsyncioTestCase):
    def setUp(self):
        TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

    async def test_valid_bytes(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            file_path = root / VALID_META_OBJ.paste_id
            await helpers.write_paste(file_path, VALID_META_OBJ, b"testing")
            self.assertTrue(file_path.is_file())

    async def test_valid_generator(self):
        async def generate_content():
            yield b"testing"

        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            file_path = root / VALID_META_OBJ.paste_id
            await helpers.write_paste(file_path, VALID_META_OBJ, generate_content())
            self.assertTrue(file_path.is_file())


class TestReadPasteMeta(IsolatedAsyncioTestCase):
    def setUp(self):
        TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

    async def test_valid(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            file_path = root / "file"
            with open(file_path, "wt") as fo:
                fo.write(VALID_META_OBJ.json() + "\n")
            meta = await helpers.read_paste_meta(file_path)
            self.assertEqual(meta.paste_id, VALID_META_OBJ.paste_id)


class TestReadPasteContent(IsolatedAsyncioTestCase):
    def setUp(self):
        TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

    async def test_valid(self):
        with TemporaryDirectory(dir=TEST_DATA_PATH) as root:
            root = Path(root)
            file_path = root / "file"
            content = "hello"
            with open(file_path, "wt") as fo:
                fo.write(f"\n{content}")
            reader = helpers.read_paste_content(file_path)
            line = await reader.__anext__()
            self.assertEqual(line.decode(), content)
            await reader.aclose()


class TestGetFormDatetime(TestCase):
    def test_valid_dt(self):
        self.assertIsInstance(helpers.get_form_datetime(VALID_DT_ISO_STRING), datetime)

    def test_valid_none(self):
        self.assertIsNone(helpers.get_form_datetime(None))

    def test_invalid(self):
        self.assertRaises(ValueError, helpers.get_form_datetime, "202A-07-26")

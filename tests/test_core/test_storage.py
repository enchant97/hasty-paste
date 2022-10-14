from datetime import datetime
from pathlib import Path
from shutil import rmtree
from unittest import IsolatedAsyncioTestCase

from paste_bin import helpers
from paste_bin.core.storage.disk import DiskStorage

TEST_DATA_PATH = Path("data/tests")
VALID_META_OBJ = helpers.PasteMeta(
    paste_id="te1200aa",
    creation_dt=datetime.utcnow(),
)


class TestDiskStorage(IsolatedAsyncioTestCase):
    _paste_root = TEST_DATA_PATH.joinpath("disk-storage")
    def setUp(self):
        self._paste_root.mkdir(parents=True, exist_ok=True)
        self._storage = DiskStorage(self._paste_root)

    def tearDown(self):
        rmtree(self._paste_root)

    def test__create_paste_path__valid(self):
        paste_id = "1234ABCD"
        expected_result = self._paste_root.joinpath(paste_id[:2], paste_id[2:])
        self.assertEqual(self._storage._create_paste_path(paste_id), expected_result)
        self.assertFalse(self._paste_root.joinpath(paste_id[:2]).is_dir())

    def test__create_paste_path__valid_mkdir(self):
        paste_id = "1234ABCE"
        expected_result = self._paste_root.joinpath(paste_id[:2], paste_id[2:])
        self.assertEqual(self._storage._create_paste_path(paste_id, True), expected_result)
        self.assertTrue(self._paste_root.joinpath(paste_id[:2]).is_dir())

    def test__create_paste_path__invalid_id(self):
        paste_id = "12"
        self.assertRaises(
            ValueError,
            self._storage._create_paste_path,
            paste_id,
            False,
        )
        self.assertRaises(
            ValueError,
            self._storage._create_paste_path,
            paste_id,
            True,
        )

    async def test__write_paste__valid_bytes(self):
        file_path = self._paste_root / VALID_META_OBJ.paste_id[:2] / VALID_META_OBJ.paste_id[2:]
        await self._storage.write_paste(VALID_META_OBJ.paste_id, b"testing", VALID_META_OBJ)
        self.assertTrue(file_path.is_file())

    async def test__write_paste__valid_generator(self):
        async def generate_content():
            yield b"testing"

        file_path = self._paste_root / VALID_META_OBJ.paste_id[:2] / VALID_META_OBJ.paste_id[2:]
        await self._storage.write_paste(VALID_META_OBJ.paste_id, generate_content(), VALID_META_OBJ)
        self.assertTrue(file_path.is_file())

    async def test__read_paste_meta__valid(self):
        (self._paste_root / "re").mkdir(parents=True, exist_ok=True)
        file_path = self._paste_root / "re" / "adpastemetavalid"
        with open(file_path, "wt") as fo:
            fo.write(VALID_META_OBJ.json() + "\n")
        meta = await self._storage.read_paste_meta("readpastemetavalid")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.paste_id, VALID_META_OBJ.paste_id)

    async def test__read_paste_raw__valid(self):
        (self._paste_root / "re").mkdir(parents=True, exist_ok=True)
        file_path = self._paste_root / "re" / "adpasterawvalid"
        content = "hello"
        with open(file_path, "wt") as fo:
            fo.write(f"\n{content}")

        raw = await self._storage.read_paste_raw("readpasterawvalid")
        self.assertIsNotNone(raw)
        self.assertEqual(raw.decode(), content)

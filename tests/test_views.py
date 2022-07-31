from datetime import datetime
from os import environ
from pathlib import Path
from shutil import rmtree
from unittest import IsolatedAsyncioTestCase

from paste_bin import helpers
from paste_bin.main import create_app, _reset_app

TEST_DATA_PATH = Path("data/tests/quart")


async def write_test_paste(content: bytes):
    meta = helpers.PasteMeta(
        paste_id=helpers.create_paste_id(),
        creation_dt=datetime.utcnow(),
    )
    paste_path = helpers.create_paste_path(TEST_DATA_PATH, meta.paste_id, True)

    await helpers.write_paste(paste_path, meta, content)

    return meta.paste_id


class QuartAppTestCase(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        environ["PASTE_ROOT"] = str(TEST_DATA_PATH)

        self.app = create_app()

    def tearDown(self) -> None:
        _reset_app()
        rmtree(TEST_DATA_PATH)

    def new_client(self):
        return self.app.test_client()


class TestIndex(QuartAppTestCase):
    async def test_valid(self):
        client = self.new_client()
        response = await client.get("/")
        data = await response.get_data(as_text=True)

        self.assertIn("Hasty Paste", data)


class TestNewPaste(QuartAppTestCase):
    async def test_valid_get(self):
        client = self.new_client()
        response = await client.get("/new")
        data = await response.get_data(as_text=True)

        self.assertIn("New", data)

    async def test_valid_post(self):
        client = self.new_client()
        response = await client.post(
            "/new",
            form={
                "paste-content": "hello",
            },
            follow_redirects=False,
        )

        self.assertTrue(response.status_code, 302)

        paste_id = response.location.split("/")[-1]

        paste_path = helpers.create_paste_path(TEST_DATA_PATH, paste_id)

        self.assertTrue(paste_path.is_file())


class TestViewPaste(QuartAppTestCase):
    async def test_valid(self):
        content = b"test valid view"
        paste_id = await write_test_paste(content)
        client = self.new_client()
        response = await client.get(f"/{paste_id}")
        data = await response.get_data(as_text=False)

        self.assertIn(b"View", data)
        self.assertIn(content, data)

    async def test_invalid_not_found(self):
        client = self.new_client()
        response = await client.get(f"/testing123")

        self.assertEqual(404, response.status_code)

    async def test_invalid_too_short(self):
        client = self.new_client()
        response = await client.get(f"/1")

        self.assertEqual(404, response.status_code)

    async def test_valid_raw(self):
        content = b"test valid view raw"
        paste_id = await write_test_paste(content)
        client = self.new_client()
        response = await client.get(f"/{paste_id}/raw")
        data = await response.get_data(as_text=False)

        self.assertNotIn(b"View", data)
        self.assertIn(content, data)

    async def test_invalid_raw_not_found(self):
        client = self.new_client()
        response = await client.get(f"/testing123/raw")

        self.assertEqual(404, response.status_code)

    async def test_invalid_raw_too_short(self):
        client = self.new_client()
        response = await client.get(f"/1/raw")

        self.assertEqual(404, response.status_code)

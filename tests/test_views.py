from datetime import datetime
from os import environ
from pathlib import Path
from shutil import rmtree
from unittest import IsolatedAsyncioTestCase

from paste_bin.core import helpers
from paste_bin.core.models import PasteApiCreate, PasteMeta
from paste_bin.core.paste_handler import get_handler
from paste_bin.main import _reset_app, create_app

TEST_DATA_PATH = Path("data/tests/quart")


async def write_test_paste(content: bytes):
    meta = PasteMeta(
        paste_id=helpers.create_paste_id(),
        creation_dt=datetime.utcnow(),
    )

    await get_handler()._storage.write_paste(meta.paste_id, content, meta)

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

        paste_path = TEST_DATA_PATH / paste_id[:2] / paste_id[2:]

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
        paste_id = "testing123"
        routes = (
            f"/{paste_id}",
            f"/{paste_id}/raw",
        )

        for route in routes:
            with self.subTest():
                client = self.new_client()
                response = await client.get(route)

                self.assertEqual(404, response.status_code)

    async def test_invalid_too_short(self):
        paste_id = "1"
        routes = (
            f"/{paste_id}",
            f"/{paste_id}/raw",
        )

        for route in routes:
            with self.subTest():
                client = self.new_client()
                response = await client.get(route)

                self.assertEqual(404, response.status_code)

    async def test_valid_raw(self):
        content = b"test valid view raw"
        paste_id = await write_test_paste(content)
        client = self.new_client()
        response = await client.get(f"/{paste_id}/raw")
        data = await response.get_data(as_text=False)

        self.assertNotIn(b"View", data)
        self.assertIn(content, data)


class TestApiNewPaste(QuartAppTestCase):
    async def test_valid(self):
        client = self.new_client()
        response = await client.post(
            "/api/pastes",
            headers={
                "Content-Type": "application/json",
            },
            data=PasteApiCreate(
                content="test api create",
            ).json(),
        )

        self.assertEqual(201, response.status_code)

        data = await response.get_json()

        paste_id = data["paste_id"]
        paste_path = paste_path = TEST_DATA_PATH / paste_id[:2] / paste_id[2:]

        self.assertTrue(paste_path.is_file())


class TestApiNewSimplePaste(QuartAppTestCase):
    async def test_valid(self):
        client = self.new_client()
        response = await client.post(
            "/api/pastes/simple",
            data="test paste simple api create"
        )

        self.assertEqual(201, response.status_code)

        paste_id = await response.get_data(True)
        paste_path = paste_path = TEST_DATA_PATH / paste_id[:2] / paste_id[2:]

        self.assertTrue(paste_path.is_file())


class TestApiView(QuartAppTestCase):
    async def test_valid_raw(self):
        content = b"test valid api view content"
        paste_id = await write_test_paste(content)
        client = self.new_client()
        response = await client.get(f"/api/pastes/{paste_id}")
        data = await response.get_data(as_text=False)

        self.assertEqual(content, data)

    async def test_valid_meta(self):
        content = b"test valid api view meta"
        paste_id = await write_test_paste(content)
        client = self.new_client()
        response = await client.get(f"/api/pastes/{paste_id}/meta")
        data = await response.get_data(as_text=True)

        self.assertIn(paste_id, data)

    async def test_invalid_not_found(self):
        paste_id = "testing123"
        routes = (
            f"/api/pastes/{paste_id}",
            f"/api/pastes/{paste_id}/meta",
            f"/api/pastes/{paste_id}/content"
        )

        for route in routes:
            with self.subTest():
                client = self.new_client()
                response = await client.get(route)

                self.assertEqual(404, response.status_code)

    async def test_invalid_too_short(self):
        paste_id = "1"
        routes = (
            f"/api/pastes/{paste_id}",
            f"/api/pastes/{paste_id}/meta",
            f"/api/pastes/{paste_id}/content"
        )

        for route in routes:
            with self.subTest():
                client = self.new_client()
                response = await client.get(route)

                self.assertEqual(404, response.status_code)

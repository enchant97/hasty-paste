from datetime import datetime
from unittest import TestCase

from paste_bin import cache, helpers

TEST_META_NO_EXPIRY = helpers.PasteMeta(
    paste_id="push",
    creation_dt=datetime.utcnow(),
)


class TestInternalCache(TestCase):
    def test_cache_len(self):
        the_cache = cache.InternalCache(None, 4)
        self.assertEqual(0, the_cache.cache_len)

        the_cache._cache["test"] = None
        self.assertEqual(1, the_cache.cache_len)

    def test_cache_push(self):
        the_cache = cache.InternalCache(None, 4)
        paste_id = "push_meta"

        the_cache.push_paste_meta(paste_id, TEST_META_NO_EXPIRY)
        self.assertEqual(the_cache._cache[paste_id].meta, TEST_META_NO_EXPIRY)

    def test_cache_push_rollover(self):
        the_cache = cache.InternalCache(None, 3)

        to_cache = [
            helpers.PasteMeta(
                paste_id="push-rollover-1",
                creation_dt=datetime.utcnow(),
            ),
            helpers.PasteMeta(
                paste_id="push-rollover-2",
                creation_dt=datetime.utcnow(),
            ),
            helpers.PasteMeta(
                paste_id="push-rollover-3",
                creation_dt=datetime.utcnow(),
            ),
            helpers.PasteMeta(
                paste_id="push-rollover-4",
                creation_dt=datetime.utcnow(),
            ),
        ]

        for item in to_cache:
            the_cache.push_paste_meta(item.paste_id, item)

        self.assertEqual(len(the_cache._cache), 3)
        self.assertIsNone(the_cache._cache.get("push-rollover-1"))

    def test_cache_get(self):
        the_cache = cache.InternalCache(None, 4)
        paste_id = "get_meta"

        the_cache._cache[paste_id] = cache.InternalCacheItem(
            meta=TEST_META_NO_EXPIRY,
        )
        self.assertEqual(the_cache.get_paste_meta(
            paste_id), TEST_META_NO_EXPIRY)

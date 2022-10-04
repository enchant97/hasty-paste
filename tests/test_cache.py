from datetime import datetime
from unittest import TestCase

from paste_bin import cache, helpers

TEST_META_NO_EXPIRY = helpers.PasteMeta(
    paste_id="push",
    creation_dt=datetime.utcnow(),
)

class TestInternalCache(TestCase):
    def test_cache_len(self):
        the_cache = cache.InternalCache(4)
        self.assertEqual(0, the_cache.cache_len)

        the_cache._cache["test"] = None
        self.assertEqual(1, the_cache.cache_len)

    def test_cache_push(self):
        the_cache = cache.InternalCache(4)
        paste_id = "push_meta"

        the_cache.push_paste_meta(paste_id, TEST_META_NO_EXPIRY)
        self.assertEqual(the_cache._cache[paste_id].meta, TEST_META_NO_EXPIRY)

    def test_cache_get(self):
        the_cache = cache.InternalCache(4)
        paste_id = "get_meta"

        the_cache._cache[paste_id] = cache.InternalCacheItem(
            meta=TEST_META_NO_EXPIRY,
        )
        self.assertEqual(the_cache.get_paste_meta(paste_id), TEST_META_NO_EXPIRY)

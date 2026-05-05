import tempfile
import unittest
from pathlib import Path

from skyeye.storage.local_store import LocalObjectStore


class LocalObjectStoreTests(unittest.TestCase):
    def test_put_bytes_returns_local_uri_and_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir))

            uri = store.put_bytes("persons/video-1/person-1/crops/obs-1.jpg", b"image-bytes", "image/jpeg")

            self.assertEqual(uri, "local://persons/video-1/person-1/crops/obs-1.jpg")
            self.assertEqual(
                (Path(tmpdir) / "persons" / "video-1" / "person-1" / "crops" / "obs-1.jpg").read_bytes(),
                b"image-bytes",
            )

    def test_resolve_uri_returns_path_inside_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir))
            uri = store.put_bytes("frames/video-1/frame-1.jpg", b"x", "image/jpeg")

            resolved = store.resolve_uri(uri)

            self.assertEqual(resolved, Path(tmpdir) / "frames" / "video-1" / "frame-1.jpg")

    def test_rejects_unsafe_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir))

            with self.assertRaises(ValueError):
                store.put_bytes("../escape.jpg", b"x", "image/jpeg")


if __name__ == "__main__":
    unittest.main()

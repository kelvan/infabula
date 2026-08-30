"""Avatar upload: a household member's profile photo, stored on the
data volume and visible only to accounts that share a baby with them."""

import io

from PIL import Image


def make_png(size=(300, 200), color=(200, 50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    buf.seek(0)
    return buf


class TestUpload:
    async def test_upload_and_fetch(self, client, logged_in):
        me = await logged_in()
        res = await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(), "image/png")},
        )
        assert res.status_code == 200
        got = await client.get(f"/api/users/{me}/avatar")
        assert got.status_code == 200
        assert got.headers["content-type"] == "image/webp"

    async def test_has_avatar_reflected_on_me(self, client, logged_in):
        await logged_in()
        await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(), "image/png")},
        )
        me = (await client.get("/api/auth/me")).json()
        assert me["has_avatar"] is True

    async def test_rejects_non_image(self, client, logged_in):
        await logged_in()
        res = await client.post(
            "/api/auth/me/avatar",
            files={"file": ("nope.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert res.status_code == 400

    async def test_rejects_formats_outside_the_allowlist(self, client, logged_in):
        """Only the handful of formats real cameras/browsers actually
        produce are decoded — every other Pillow-supported format is a
        rarely-fuzzed decoder run on attacker-controlled bytes for no
        real benefit."""
        await logged_in()
        buf = io.BytesIO()
        Image.new("RGB", (100, 100)).save(buf, "BMP")
        buf.seek(0)
        res = await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.bmp", buf, "image/bmp")},
        )
        assert res.status_code == 400

    async def test_rejects_oversized_upload(self, client, logged_in):
        await logged_in()
        huge = io.BytesIO(b"\x00" * (8 * 1024 * 1024 + 1))
        res = await client.post(
            "/api/auth/me/avatar",
            files={"file": ("big.png", huge, "image/png")},
        )
        assert res.status_code == 400

    async def test_non_square_is_cropped_to_square(self, client, logged_in):
        me = await logged_in()
        await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(size=(400, 100)), "image/png")},
        )
        got = await client.get(f"/api/users/{me}/avatar")
        img = Image.open(io.BytesIO(got.content))
        assert img.size == (256, 256)


class TestDelete:
    async def test_delete_clears_it(self, client, logged_in):
        me = await logged_in()
        await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(), "image/png")},
        )
        res = await client.delete("/api/auth/me/avatar")
        assert res.status_code == 200
        assert (await client.get(f"/api/users/{me}/avatar")).status_code == 404

    async def test_delete_when_none_is_not_an_error(self, client, logged_in):
        await logged_in()
        res = await client.delete("/api/auth/me/avatar")
        assert res.status_code == 200


class TestVisibility:
    async def test_no_avatar_yet_is_404(self, client, logged_in):
        me = await logged_in()
        assert (await client.get(f"/api/users/{me}/avatar")).status_code == 404

    async def test_visible_to_someone_sharing_a_baby(
        self, client, logged_in, baby_factory, user_factory
    ):
        owner = await logged_in("owner@example.com")
        baby_id = await baby_factory(owner)
        await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(), "image/png")},
        )
        friend = await user_factory(email="friend@example.com")
        await client.post(
            f"/api/babies/{baby_id}/access",
            json={"email": "friend@example.com", "role": "viewer"},
        )
        await client.post("/api/auth/logout")
        friend_login = await client.post(
            "/api/auth/login",
            json={"email": "friend@example.com", "password": "password123"},
        )
        assert friend_login.status_code == 200
        res = await client.get(f"/api/users/{owner}/avatar")
        assert res.status_code == 200
        assert friend != owner

    async def test_hidden_from_an_unrelated_account(
        self, client, logged_in, baby_factory, user_factory
    ):
        owner = await logged_in("owner@example.com")
        await baby_factory(owner)
        await client.post(
            "/api/auth/me/avatar",
            files={"file": ("photo.png", make_png(), "image/png")},
        )
        await client.post("/api/auth/logout")
        await user_factory(email="stranger@example.com")
        stranger_login = await client.post(
            "/api/auth/login",
            json={"email": "stranger@example.com", "password": "password123"},
        )
        assert stranger_login.status_code == 200
        res = await client.get(f"/api/users/{owner}/avatar")
        assert res.status_code == 403

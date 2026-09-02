"""The PWA install surface: service worker and manifest.

The service worker specifically has to be reachable unauthenticated and
served from the site root — both are easy to silently break (an auth
gate that grows a new path, a route that moves under /static/), and
either one quietly kills Android's install eligibility with no visible
error anywhere in the app.
"""


class TestServiceWorker:
    async def test_reachable_without_a_session(self, client):
        res = await client.get("/sw.js")
        assert res.status_code == 200

    async def test_not_a_static_asset(self, client):
        """A service worker's default scope is the directory it's
        served from — under /static/ it could only ever control static
        assets, never the app itself."""
        res = await client.get("/sw.js")
        assert res.status_code == 200
        # And the old location should be gone, not just duplicated.
        assert (await client.get("/static/sw.js")).status_code == 404

    async def test_is_not_cached_like_static_assets(self, client):
        """Everything under /static/ is served immutable for a year;
        a service worker must never be, or an update to it would be
        stuck behind that cache indefinitely."""
        res = await client.get("/sw.js")
        assert "no-cache" in res.headers["cache-control"]

    async def test_correct_content_type(self, client):
        res = await client.get("/sw.js")
        assert "javascript" in res.headers["content-type"]


class TestManifest:
    async def test_reachable_without_a_session(self, client):
        res = await client.get("/manifest.json")
        assert res.status_code == 200

    async def test_not_cached_like_static_assets(self, client):
        """Icon URLs inside carry the asset version; the manifest itself
        must stay fetchable so a changed icon is actually picked up."""
        res = await client.get("/manifest.json")
        assert "no-cache" in res.headers["cache-control"]

    async def test_old_static_location_is_gone(self, client):
        """Anything still linking /static/manifest.json would get the
        immutable-cached copy forever — it must 404, not be duplicated."""
        assert (await client.get("/static/manifest.json")).status_code == 404

    async def test_icon_urls_are_versioned_by_path(self, client):
        """/static/ is immutable for a year and Chrome's WebAPK server
        caches too — the icon URL has to be a genuinely new path each
        deploy, not the same path with a query."""
        manifest = (await client.get("/manifest.json")).json()
        assert manifest["icons"]
        assert all(i["src"].startswith("/app-icon/") for i in manifest["icons"])

    async def test_app_icon_route_serves_png_uncached(self, client):
        src = (await client.get("/manifest.json")).json()["icons"][0]["src"]
        res = await client.get(src)
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"
        assert "no-cache" in res.headers["cache-control"]

    async def test_app_icon_route_rejects_a_bogus_name(self, client):
        assert (await client.get("/app-icon/123/../secret.png")).status_code == 404
        assert (await client.get("/app-icon/123/logo.svg")).status_code == 404

    async def test_start_url_matches_what_the_service_worker_controls(self, client):
        """If these ever diverge, Chrome won't consider the app
        installable — the service worker has to control the page the
        manifest says to launch."""
        manifest = (await client.get("/manifest.json")).json()
        assert manifest["start_url"] == "/"

    async def test_has_the_icon_sizes_android_expects(self, client):
        manifest = (await client.get("/manifest.json")).json()
        sizes = {icon["sizes"] for icon in manifest["icons"]}
        assert "192x192" in sizes
        assert "512x512" in sizes

    async def test_has_a_maskable_icon(self, client):
        """Without one, Android falls back to boxing the icon on a
        white circle instead of using the adaptive-icon shape."""
        manifest = (await client.get("/manifest.json")).json()
        assert any("maskable" in icon["purpose"] for icon in manifest["icons"])

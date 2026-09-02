"""Per-baby nap threshold: the minutes cutoff between a nap and night
sleep in stats, moved off a fixed global constant onto each baby."""


class TestNapThreshold:
    async def test_defaults_to_240(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["nap_threshold_min"] == 240

    async def test_save_and_read_back(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.put(
            f"/api/babies/{baby_id}", json={"nap_threshold_min": 180}
        )
        assert res.status_code == 200
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["nap_threshold_min"] == 180

    async def test_rejects_out_of_range(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.put(f"/api/babies/{baby_id}", json={"nap_threshold_min": 5})
        assert res.status_code == 400

    async def test_rejects_non_int(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.put(
            f"/api/babies/{baby_id}", json={"nap_threshold_min": "a lot"}
        )
        assert res.status_code == 400

    async def test_invalid_threshold_does_not_save_other_fields_either(
        self, client, logged_in, baby_factory
    ):
        """A rejected threshold shouldn't silently let a name change
        through in the same request."""
        baby_id = await baby_factory(await logged_in(), name="Original")
        res = await client.put(
            f"/api/babies/{baby_id}",
            json={"name": "Changed", "nap_threshold_min": 99999},
        )
        assert res.status_code == 400
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["name"] == "Original"


class TestBottleDefaultContent:
    async def test_defaults_to_unset(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["bottle_default_content"] == ""

    async def test_save_and_read_back(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        assert (
            await client.put(
                f"/api/babies/{baby_id}", json={"bottle_default_content": "formula"}
            )
        ).status_code == 200
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["bottle_default_content"] == "formula"

    async def test_empty_string_clears_it(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        await client.put(
            f"/api/babies/{baby_id}", json={"bottle_default_content": "abgepumpt"}
        )
        await client.put(
            f"/api/babies/{baby_id}", json={"bottle_default_content": ""}
        )
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["bottle_default_content"] == ""

    async def test_rejects_an_unknown_value(self, client, logged_in, baby_factory):
        baby_id = await baby_factory(await logged_in())
        res = await client.put(
            f"/api/babies/{baby_id}", json={"bottle_default_content": "oat"}
        )
        assert res.status_code == 400

    async def test_bad_value_does_not_save_the_name_either(
        self, client, logged_in, baby_factory
    ):
        baby_id = await baby_factory(await logged_in(), name="Original")
        res = await client.put(
            f"/api/babies/{baby_id}",
            json={"name": "Changed", "bottle_default_content": "oat"},
        )
        assert res.status_code == 400
        babies = (await client.get("/api/babies")).json()
        mine = next(b for b in babies if b["id"] == baby_id)
        assert mine["name"] == "Original"

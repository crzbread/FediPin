import unittest

from app import USERNAME, create_app, normalize_public_base_url


PUBLIC_URL = "https://fedipin.example"
ACTOR_URL = f"{PUBLIC_URL}/users/{USERNAME}"
ACCOUNT = f"acct:{USERNAME}@fedipin.example"


class FediPinTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # Flask 的 test client 不需要真的開網路服務，測試會更快也更穩定。
        self.client = create_app(f"{PUBLIC_URL}/").test_client()

    def test_home_shows_account_and_actor_url(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(f"@{USERNAME}@fedipin.example", response.get_data(as_text=True))
        self.assertIn(ACTOR_URL, response.get_data(as_text=True))

    def test_app_exposes_copyable_account(self) -> None:
        app = create_app(PUBLIC_URL)

        self.assertEqual(
            app.config["FEDIVERSE_ACCOUNT"], f"@{USERNAME}@fedipin.example"
        )
        self.assertEqual(app.config["ACTOR_URL"], ACTOR_URL)
        self.assertEqual(app.config["PUBLIC_BASE_URL"], PUBLIC_URL)

    def test_webfinger_returns_actor_link(self) -> None:
        response = self.client.get(
            "/.well-known/webfinger", query_string={"resource": ACCOUNT}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("application/jrd+json"))
        self.assertEqual(response.json["subject"], ACCOUNT)
        self.assertEqual(response.json["links"][0]["href"], ACTOR_URL)

    def test_webfinger_rejects_missing_or_unknown_resource(self) -> None:
        missing = self.client.get("/.well-known/webfinger")
        unknown = self.client.get(
            "/.well-known/webfinger",
            query_string={"resource": "acct:other@fedipin.example"},
        )

        self.assertEqual(missing.status_code, 400)
        self.assertEqual(unknown.status_code, 404)

    def test_actor_returns_activitypub_profile(self) -> None:
        response = self.client.get(f"/users/{USERNAME}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content_type.startswith("application/activity+json"))
        self.assertTrue(
            {
                "@context",
                "id",
                "type",
                "preferredUsername",
                "name",
                "summary",
                "inbox",
                "url",
            }.issubset(response.json)
        )
        self.assertEqual(response.json["id"], ACTOR_URL)
        self.assertEqual(response.json["inbox"], f"{ACTOR_URL}/inbox")
        self.assertEqual(response.json["preferredUsername"], USERNAME)

    def test_inbox_accepts_any_body(self) -> None:
        response = self.client.post(
            f"/users/{USERNAME}/inbox",
            data="這不是 JSON",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)

    def test_public_url_must_be_configured_and_use_https(self) -> None:
        with self.assertRaises(RuntimeError):
            normalize_public_base_url(None)
        with self.assertRaises(RuntimeError):
            normalize_public_base_url("http://localhost:5000")
        with self.assertRaises(RuntimeError):
            normalize_public_base_url("https://fedipin.example/not-allowed")


if __name__ == "__main__":
    unittest.main()

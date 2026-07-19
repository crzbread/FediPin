"""FediPin：一個只負責讓 Fediverse 搜尋到的最小 ActivityPub 身分。"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request


# 自動讀取專案根目錄的 .env
load_dotenv()


# 這三個欄位就是 Fediverse 上會顯示的基本個人資料。
USERNAME = "me"
DISPLAY_NAME = "DBB"
SUMMARY = "一個最小的 Python ActivityPub 實驗。"


def normalize_public_base_url(value: str | None) -> str:
    """檢查公開網址，並移除尾端斜線，避免組合 URL 時出現 //。"""
    if not value:
        raise RuntimeError(
            "尚未設定 PUBLIC_BASE_URL。"
            "請先設定公開 HTTPS 網址，例如：https://example.ngrok-free.app"
        )

    public_base_url = value.rstrip("/")
    parsed_url = urlparse(public_base_url)

    # ActivityPub 身分會綁定網域，所以不能使用 localhost 或不完整的網址。
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise RuntimeError(
            "PUBLIC_BASE_URL 必須是完整的 HTTPS 網址，"
            "例如：https://example.ngrok-free.app"
        )

    # 第一版只接受純網域，避免網址路徑讓 WebFinger 帳號與 Actor 路徑對不上。
    if (
        parsed_url.path
        or parsed_url.params
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise RuntimeError("PUBLIC_BASE_URL 只能包含 HTTPS 網域，不可包含路徑、參數或片段。")

    return public_base_url


def create_app(public_base_url: str | None = None) -> Flask:
    """建立 Flask 應用程式；測試時可以直接傳入假的公開網址。"""
    app = Flask(__name__)
    base_url = normalize_public_base_url(
        public_base_url if public_base_url is not None else os.getenv("PUBLIC_BASE_URL")
    )

    actor_url = f"{base_url}/users/{USERNAME}"
    inbox_url = f"{actor_url}/inbox"
    domain = urlparse(base_url).netloc
    account = f"acct:{USERNAME}@{domain}"

    # 保存在 Flask 設定裡，啟動時就能直接顯示可複製的完整帳號。
    app.config["PUBLIC_BASE_URL"] = base_url
    app.config["FEDIVERSE_ACCOUNT"] = f"@{USERNAME}@{domain}"
    app.config["ACTOR_URL"] = actor_url

    @app.get("/")
    def home() -> Response:
        # 這一頁是給人看的；真正讓 Mastodon 搜尋的是下方兩個 JSON 端點。
        html = f"""<!doctype html>
<html lang="zh-Hant">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{DISPLAY_NAME} · FediPin</title>
    <style>
      body {{
        max-width: 42rem;
        margin: 12vh auto;
        padding: 0 1.5rem;
        color: #202124;
        font-family: system-ui, sans-serif;
        line-height: 1.6;
      }}
      .card {{ padding: 2rem; border: 1px solid #ddd; border-radius: 1rem; }}
      .account {{ font-size: 1.25rem; font-weight: 700; }}
      a {{ color: #5b45d6; overflow-wrap: anywhere; }}
    </style>
  </head>
  <body>
    <main class="card">
      <h1>{DISPLAY_NAME}</h1>
      <p>{SUMMARY}</p>
      <p class="account">@{USERNAME}@{domain}</p>
      <p>ActivityPub Actor：<a href="{actor_url}">{actor_url}</a></p>
    </main>
  </body>
</html>"""
        return Response(html, content_type="text/html; charset=utf-8")

    @app.get("/.well-known/webfinger")
    def webfinger() -> tuple[Response, int] | Response:
        # WebFinger 先把「@使用者@網域」轉成 Actor JSON 的公開位置。
        resource = request.args.get("resource")
        if resource is None:
            return jsonify(error="缺少 resource 查詢參數"), 400
        if resource != account:
            return jsonify(error="找不到這個帳號"), 404

        response = jsonify(
            subject=account,
            links=[
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": actor_url,
                }
            ],
        )
        response.content_type = "application/jrd+json; charset=utf-8"
        return response

    @app.get(f"/users/{USERNAME}")
    def actor() -> Response:
        # Actor 就像 Fediverse 上的公開個人名片，欄位名稱來自 ActivityStreams。
        response = jsonify(
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": actor_url,
                "type": "Person",
                "preferredUsername": USERNAME,
                "name": DISPLAY_NAME,
                "summary": SUMMARY,
                "inbox": inbox_url,
                "url": actor_url,
            }
        )
        response.content_type = "application/activity+json; charset=utf-8"
        return response

    @app.post(f"/users/{USERNAME}/inbox")
    def inbox() -> tuple[str, int]:
        # 第一版只確認收到請求，不讀取內容，因此任意內容都不會讓服務崩潰。
        return "", 202

    return app


if __name__ == "__main__":
    # PORT 是本機使用的埠號；公開網址仍以 PUBLIC_BASE_URL 為準。
    port_text = os.getenv("PORT", "5057")
    try:
        port = int(port_text)
    except ValueError as error:
        raise RuntimeError("PORT 必須是數字，例如：5057") from error

    app = create_app()

    # 把最常用的資訊獨立顯示，使用者可以直接複製到 Fediverse 搜尋。
    print("\nFediPin 已準備啟動")
    print(f"可搜尋帳號：{app.config['FEDIVERSE_ACCOUNT']}")
    print(f"公開首頁：{app.config['PUBLIC_BASE_URL']}\n", flush=True)

    app.run(host="0.0.0.0", port=port)

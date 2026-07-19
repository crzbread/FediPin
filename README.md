# FediPin

用一小段 Python 程式，建立能在 Fediverse（例如 Mastodon）上被搜尋到的 ActivityPub 身分。

目前支援 WebFinger、Actor、Inbox，並附上一個簡單的個人頁面；暫時不支援發文、追蹤或登入。

## 快速開始

開始前，請先準備好 Python 3.10 以上版本和 [ngrok](https://ngrok.com/)。

建立虛擬環境、安裝套件，並複製一份設定檔：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

接著啟動 ngrok：

```bash
ngrok http 5057
```

將 ngrok 顯示的 HTTPS 網址填入 `.env` 的 `PUBLIC_BASE_URL`，再開一個終端機啟動 FediPin：

```bash
source .venv/bin/activate
python app.py
```

啟動後，終端機會顯示可直接複製的 Fediverse 帳號：

```text
FediPin 已準備啟動
可搜尋帳號：@me@你的網址.ngrok-free.app
公開首頁：https://你的網址.ngrok-free.app
```

複製「可搜尋帳號」後面的內容，就能在任何 Fediverse 站台中搜尋這個帳號。

## 交給 AI 執行

> 請依照 README 的步驟，在這個資料夾中安裝並啟動 FediPin 和 ngrok。取得公開網址後，請更新 `.env`，最後告訴我完整的 Fediverse 帳號。

## 測試

```bash
source .venv/bin/activate
python -m unittest -v
```

> 每次 ngrok 網址變更，帳號也會跟著改變。目前 FediPin 只能讓其他 Fediverse 使用者搜尋到這個帳號，還不能用來發文或追蹤其他帳號。

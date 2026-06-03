"""Google Drive 上傳邏輯。

使用 OAuth 憑證（你本人授權一次後存下的 token），
伺服器以你的身份把賓客上傳的照片放進指定資料夾。
賓客完全不需要登入，也看不到資料夾內容。
"""
import io
import json
import os
import threading
from urllib.parse import urlparse

import httplib2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import config

# Drive API client 不是 thread-safe，加鎖保護
_lock = threading.Lock()
_service = None


def _build_http():
    """建立 httplib2.Http，若環境設定了 HTTP(S) proxy 則套用。

    一般雲端部署（Render 等）不會有 proxy，會回傳 None（用預設連線）；
    僅在公司網路 / 沙箱等有 proxy 的環境才套用，方便本機測試。
    """
    proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    proxy_info = httplib2.ProxyInfo(
        proxy_type=httplib2.socks.PROXY_TYPE_HTTP,
        proxy_host=parsed.hostname,
        proxy_port=parsed.port or 3128,
    )
    return httplib2.Http(proxy_info=proxy_info)



def _load_credentials() -> Credentials:
    """從 token 檔或環境變數載入憑證，必要時自動刷新。"""
    creds = None

    if config.GOOGLE_TOKEN_JSON:
        info = json.loads(config.GOOGLE_TOKEN_JSON)
        creds = Credentials.from_authorized_user_info(info, config.SCOPES)
    else:
        try:
            creds = Credentials.from_authorized_user_file(
                config.GOOGLE_TOKEN_FILE, config.SCOPES
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"找不到授權檔 {config.GOOGLE_TOKEN_FILE}，請先執行： python authorize.py"
            ) from exc

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # 刷新後存回檔案（部署用環境變數時略過）
            if not config.GOOGLE_TOKEN_JSON:
                with open(config.GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
        else:
            raise RuntimeError("授權已失效，請重新執行： python authorize.py")

    return creds


def get_service():
    """取得（並快取）Drive API service。"""
    global _service
    with _lock:
        if _service is None:
            creds = _load_credentials()
            proxied_http = _build_http()
            if proxied_http is not None:
                authed_http = AuthorizedHttp(creds, http=proxied_http)
                _service = build(
                    "drive", "v3", http=authed_http, cache_discovery=False
                )
            else:
                _service = build(
                    "drive", "v3", credentials=creds, cache_discovery=False
                )
        return _service


def upload_file(file_bytes: bytes, filename: str, mime_type: str) -> str:
    """把單一檔案上傳到設定的資料夾，回傳 Drive 檔案 ID。"""
    if not config.DRIVE_FOLDER_ID:
        raise RuntimeError("尚未設定 DRIVE_FOLDER_ID，請在 .env 填入目標資料夾 ID。")

    service = get_service()

    metadata = {
        "name": filename,
        "parents": [config.DRIVE_FOLDER_ID],
    }
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mime_type or "application/octet-stream",
        resumable=True,
    )

    with _lock:
        created = (
            service.files()
            .create(body=metadata, media_body=media, fields="id", supportsAllDrives=True)
            .execute()
        )
    return created["id"]


def check_ready() -> None:
    """啟動時做一次檢查，盡早發現設定問題。"""
    if not config.DRIVE_FOLDER_ID:
        raise RuntimeError("尚未設定 DRIVE_FOLDER_ID。")
    _load_credentials()

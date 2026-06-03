"""集中管理設定，從環境變數 / .env 讀取。"""
import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth
GOOGLE_CLIENT_SECRETS = os.getenv("GOOGLE_CLIENT_SECRETS", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
# 部署時也可以直接把 token.json 的內容塞進這個環境變數（避免上傳檔案）
GOOGLE_TOKEN_JSON = os.getenv("GOOGLE_TOKEN_JSON")

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "").strip()

# 伺服器
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
PORT = int(os.getenv("PORT", "8000"))

# 只允許照片 / 影片
ALLOWED_MIME_PREFIXES = ("image/", "video/")

# 上傳照片時要連同 Google Drive 的權限範圍
# drive.file 只能存取「本程式建立的檔案」，安全範圍最小
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

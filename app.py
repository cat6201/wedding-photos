"""婚禮照片上傳服務（FastAPI）。

賓客流程：掃 QR code -> 開啟上傳頁 -> 選照片 -> 上傳到新人的 Google Drive。
賓客看不到雲端硬碟內任何已上傳的照片。
"""
import datetime
import uuid

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

import config
import google_drive

app = FastAPI(title="婚禮照片上傳")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def _startup():
    try:
        google_drive.check_ready()
        print("✅ Google Drive 連線設定正常。")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Google Drive 尚未就緒：{exc}")
        print("    伺服器仍會啟動，但上傳會失敗，請先完成設定。")


@app.get("/")
def index(request: Request):
    """賓客看到的上傳頁面。"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


def _safe_filename(original: str) -> str:
    """避免檔名衝突：加上時間戳與隨機碼。"""
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    name = (original or "photo").replace("/", "_").replace("\\", "_").strip()
    return f"{stamp}_{short}_{name}"


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """接收單一檔案並上傳到 Google Drive。"""
    # 檢查類型
    if not file.content_type or not file.content_type.startswith(
        config.ALLOWED_MIME_PREFIXES
    ):
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "只接受照片或影片檔案。"},
        )

    data = await file.read()

    # 檢查大小
    if len(data) == 0:
        return JSONResponse(
            status_code=400, content={"ok": False, "error": "檔案是空的。"}
        )
    if len(data) > config.MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "ok": False,
                "error": f"檔案太大，上限為 {config.MAX_FILE_SIZE_MB}MB。",
            },
        )

    try:
        file_id = google_drive.upload_file(
            data, _safe_filename(file.filename), file.content_type
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": f"上傳失敗：{exc}"},
        )

    return {"ok": True, "id": file_id, "name": file.filename}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=config.PORT, reload=False)

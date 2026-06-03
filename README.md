# 婚禮照片上傳 💍

賓客掃 QR code → 開啟網頁 → 上傳照片／影片，照片直接進你的 Google Drive 資料夾。
**賓客不需要登入 Google，也看不到資料夾裡已上傳的任何照片。**

---

## 運作原理

- 伺服器握有「你本人」的 Google 授權（OAuth token），以你的身份把檔案放進指定資料夾。
- 賓客端只是個上傳網頁，沒有任何讀取雲端硬碟的能力。
- 權限範圍用最小的 `drive.file`，程式只能碰自己上傳的檔案。

---

## 一、安裝環境

需要 Python 3.8 以上（建議 3.10+）。

```bash
cd /build/adam/test/upload_image
python3 -m venv .venv             # 若提示找不到 venv：sudo apt install python3-venv
source .venv/bin/activate         # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 二、建立 Google 憑證（只做一次）

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)，建立一個專案（免費）。
2. 左側選 **「API 和服務」→「已啟用的 API」→ 啟用 Google Drive API**。
3. 到 **「OAuth 同意畫面」**：
   - User Type 選 **外部 (External)**。
   - 填好應用程式名稱、你的 email。
   - 在 **「測試使用者」** 加入你自己的 Gmail（重要，否則無法授權）。
4. 到 **「憑證」→「建立憑證」→「OAuth 用戶端 ID」**：
   - 應用程式類型選 **桌面應用程式 (Desktop app)**。
   - 建立後按 **下載 JSON**，把檔案改名為 `credentials.json` 放到本專案資料夾。

---

## 三、授權（只做一次）

```bash
python authorize.py
```

會開啟瀏覽器，用你的婚禮 Google 帳號登入並同意授權。
成功後會產生 `token.json`，之後伺服器就靠它運作。

> `.env` 已經幫你填好資料夾 ID（`1Bx8968xwZgscSFxH_fs83sNYflTX26iz`）。

---

## 四、啟動伺服器（本機測試）

```bash
python app.py
```

打開瀏覽器到 http://localhost:8000 ，就能看到上傳頁面、試上傳一張照片，
然後去 Google Drive 資料夾確認檔案有進去。

---

## 五、讓賓客能連上（正式上線）

賓客的手機需要連到你的伺服器，所以要有一個公開網址。最簡單免費的方式：

### 方案 A：免費雲端平台 Render（推薦）

專案已附 `render.yaml`、`Procfile`、`runtime.txt`，部署很簡單：

1. 把專案推上 GitHub（`.env`、`credentials.json`、`token.json` 已被 `.gitignore` 擋住，**不會外洩**）。
2. 先取得 `token.json` 的內容（部署用環境變數，不上傳檔案）：
   ```bash
   cat token.json
   ```
   把整段 `{...}` 複製起來備用。
3. 到 [Render](https://render.com/) → **New → Blueprint**，連接你的 GitHub repo。
   Render 會自動讀取 `render.yaml`。
4. 它會要求你填兩個標記為 `sync: false` 的環境變數：
   - `GOOGLE_TOKEN_JSON` = 上一步複製的 `token.json` 整段內容
   - `PUBLIC_BASE_URL` = 先隨便填，部署後改成 Render 給你的網址
     （例如 `https://wedding-photo-upload.onrender.com`）
   - `DRIVE_FOLDER_ID` 已寫在 `render.yaml`，不必再填。
5. 部署完成後，複製 Render 給的網址，回到該服務的 **Environment**，
   把 `PUBLIC_BASE_URL` 改成那個正式網址 → 儲存（會自動重新部署）。
6. 用瀏覽器開那個網址測試上傳一張照片，確認進到 Google Drive 資料夾。

> 注意：Render 免費方案閒置一段時間會休眠，第一位賓客連線時可能要等約 30 秒喚醒，之後就順暢。婚禮前先自己開一次網址喚醒即可。

### 方案 B：臨時對外（快速 demo，不需部署）

本機跑著 `python app.py`，另開一個視窗：

```bash
# 安裝一次 cloudflared 或 ngrok，這裡以 cloudflared 為例
cloudflared tunnel --url http://localhost:8000
```

它會給你一個公開網址，把它填到 `.env` 的 `PUBLIC_BASE_URL`，再產生 QR code。
（注意：你電腦關機網址就失效，適合測試或當天用筆電現場掛著。）

---

## 六、產生 QR code

確認 `PUBLIC_BASE_URL` 是**正式對外網址**後（本機用 `.env`，雲端用環境變數），
在能讀到該設定的環境執行：

```bash
python make_qr.py
```

會產生 `wedding_qr.png`，印出來放在婚禮現場即可。

> 小撇步：若 `make_qr.py` 在本機跑，記得先把 `.env` 的 `PUBLIC_BASE_URL`
> 暫時改成 Render 的正式網址再產生 QR code。

---


## 檔案說明

| 檔案 | 用途 |
|------|------|
| `app.py` | FastAPI 伺服器與上傳 API |
| `google_drive.py` | Google Drive 上傳邏輯 |
| `authorize.py` | 一次性 OAuth 授權，產生 token.json |
| `make_qr.py` | 產生賓客掃描用 QR code |
| `config.py` | 設定讀取 |
| `templates/upload.html` | 賓客看到的上傳頁面 |
| `render.yaml` / `Procfile` / `runtime.txt` | Render 部署設定 |
| `.env` | 你的設定（機密，勿外流） |

---

## 安全提醒

- `credentials.json`、`token.json`、`.env` 都是機密，已被 `.gitignore` 排除，請勿公開。
- 賓客頁面只有上傳功能，無法瀏覽、刪除或下載你雲端硬碟的內容。

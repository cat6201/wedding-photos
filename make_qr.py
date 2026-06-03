"""產生賓客掃描用的 QR code。

QR code 會指向 PUBLIC_BASE_URL（在 .env 設定），
賓客掃描後直接開啟上傳頁面。

執行：
    python make_qr.py
"""
import qrcode

import config


def main():
    url = config.PUBLIC_BASE_URL
    img = qrcode.make(url)
    out = "wedding_qr.png"
    img.save(out)
    print(f"✅ 已產生 QR code：{out}")
    print(f"   指向網址：{url}")
    print("   把這張圖印出來放在婚禮現場，賓客掃描即可上傳照片。")


if __name__ == "__main__":
    main()

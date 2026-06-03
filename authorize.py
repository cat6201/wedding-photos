"""一次性授權工具。

在你「本機電腦」執行一次，用你的 Google 帳號登入授權，
產生 token.json，之後伺服器就能以你的身份上傳照片。

執行：
    python authorize.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

import config


def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        config.GOOGLE_CLIENT_SECRETS, config.SCOPES
    )
    # 用固定埠號 8765，搭配 VS Code 埠號轉發，瀏覽器跳轉時會自動完成授權。
    creds = flow.run_local_server(
        host="localhost",
        port=8765,
        open_browser=False,
        prompt="consent",
        access_type="offline",
        authorization_prompt_message=(
            "\n👉 請在你自己的電腦瀏覽器打開以下網址登入並授權：\n\n{url}\n"
        ),
        success_message="授權完成！可以關閉這個分頁，回到 VS Code。",
    )

    with open(config.GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n✅ 授權成功！已存到 {config.GOOGLE_TOKEN_FILE}")
    print("   請妥善保管此檔，不要外流或上傳到公開的地方。")
    print("\n若要部署到雲端，可把以下整段內容設成環境變數 GOOGLE_TOKEN_JSON：\n")
    print(creds.to_json())


if __name__ == "__main__":
    main()

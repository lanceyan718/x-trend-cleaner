import asyncio
from playwright.async_api import async_playwright
import os

async def get_interactive_cookie():
    print("================================================================")
    print("正在为您打开一个带有界面的 Chromium 浏览器...")
    print("请在此浏览器中**登录您的 X (Twitter) 账号**。")
    print("登录成功并看到您的主页信息流后，请回到这个命令行窗口，按回车键！")
    print("================================================================")
    
    async with async_playwright() as p:
        # Launch with headless=False so you can see the UI and login
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://x.com/login")
        
        # We wait for the user to login manually and press Enter in the console
        await asyncio.to_thread(input, ">>> 当您在浏览器中登录成功后，请按回车键继续...")
        
        # After user says they are logged in, we extract the cookies
        cookies = await context.cookies()
        auth_token = next((cookie['value'] for cookie in cookies if cookie['name'] == 'auth_token'), None)
        
        if auth_token:
            print("\n✅ 成功获取到 auth_token!")
            print(f"您的 auth_token 是: {auth_token}\n")
            
            # Save it to a local file so the other scripts can read it automatically
            with open("auth_token.txt", "w") as f:
                f.write(auth_token)
            print("已将 auth_token 自动保存到当前目录的 auth_token.txt 文件中。")
            print("接下来的测试脚本会自动读取它，您不需要手动复制了。")
        else:
            print("\n❌ 未能找到 auth_token，请确认您是否已经成功登录。")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_interactive_cookie())

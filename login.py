import asyncio
import json
from typing import Optional, Dict
import requests
from datetime import datetime
from capmonster_python import TurnstileTask
from colorama import Fore, Style, init

init(autoreset=True)

def log_step(message: str, type: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "info": Fore.LIGHTCYAN_EX,
        "success": Fore.LIGHTGREEN_EX,
        "error": Fore.LIGHTRED_EX,
        "warning": Fore.LIGHTYELLOW_EX
    }
    color = colors.get(type, Fore.WHITE)
    prefix = {
        "info": "ℹ",
        "success": "✓",
        "error": "✗",
        "warning": "⚠"
    }
    print(f"{Fore.WHITE}[{timestamp}] {color}{prefix.get(type, '•')} {message}{Style.RESET_ALL}")

class LoginClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.nodepay.ai/api"
        self.capmonster = TurnstileTask(api_key)
        
    async def get_captcha_token(self) -> Optional[str]:
        try:
            task_id = self.capmonster.create_task(
                website_key='0x4AAAAAAAx1CyDNL8zOEPe7',
                website_url='https://app.nodepay.ai/login'
            )
            return self.capmonster.join_task_result(task_id).get("token")
        except Exception as e:
            log_step(f"获取验证码失败: {str(e)}", "error")
            return None

    async def login(self, email: str, password: str) -> Optional[str]:
        try:
            captcha_token = await self.get_captcha_token()
            if not captcha_token:
                return None

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'origin': 'https://app.nodepay.ai',
                'referer': 'https://app.nodepay.ai/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            json_data = {
                'user': email,
                'password': password,
                'remember_me': True,
                'recaptcha_token': captcha_token
            }

            response = requests.post(
                f"{self.base_url}/auth/login",
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            data = response.json()
            if data.get("success"):
                token = data['data']['token']
                log_step(f"登录成功: {email}", "success")
                return token
            else:
                log_step(f"登录失败: {data.get('msg', 'Unknown error')}", "error")
                return None

        except Exception as e:
            log_step(f"登录出错: {str(e)}", "error")
            return None

async def main():
    print(f"{Fore.YELLOW}NodePay 批量登录工具{Style.RESET_ALL}")
    api_key = input(f"{Fore.GREEN}请输入 Capmonster API Key: {Style.RESET_ALL}")
    
    client = LoginClient(api_key)
    successful_logins = []
    
    try:
        with open('accounts.txt', 'r', encoding='utf-8') as f:
            accounts = []
            current_account = {}
            
            for line in f:
                line = line.strip()
                if not line or line.startswith('-'):
                    if current_account.get('email') and current_account.get('password'):
                        accounts.append(current_account)
                        current_account = {}
                    continue
                    
                if line.startswith('Email:'):
                    current_account['email'] = line.replace('Email:', '').strip()
                elif line.startswith('Password:'):
                    current_account['password'] = line.replace('Password:', '').strip()
            
            # 添加最后一个账号
            if current_account.get('email') and current_account.get('password'):
                accounts.append(current_account)
        
        log_step(f"成功加载 {len(accounts)} 个账号", "success")
        
        for i, account in enumerate(accounts, 1):
            print(f"\n{Fore.CYAN}{'='*45}")
            log_step(f"正在处理账号 {i}/{len(accounts)}", "info")
            
            token = await client.login(account['email'], account['password'])
            if token:
                successful_logins.append({
                    'email': account['email'],
                    'token': token
                })
                
                # 保存新token到文件
                with open('new_tokens.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{token}\n")
                    
        print(f"\n{Fore.CYAN}{'='*45}")
        log_step("登录总结:", "info")
        log_step(f"总账号数: {len(accounts)}", "info")
        log_step(f"成功登录: {len(successful_logins)}", "success")
        print(f"{Fore.CYAN}{'='*45}\n")
        
    except FileNotFoundError:
        log_step("找不到 accounts.txt 文件", "error")
    except Exception as e:
        log_step(f"发生错误: {str(e)}", "error")

if __name__ == "__main__":
    asyncio.run(main()) 
import os
import json
import requests
import time
from datetime import datetime

# 从环境变量获取配置
target_repo = os.environ['TARGET_REPO']
token = os.environ.get('GITHUB_TOKEN')  # 可选，提供更高的API限额

def get_latest_release():
    """获取目标仓库的最新发布版本"""
    url = f"https://api.github.com/repos/{target_repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    
    return None

def load_current_version():
    """从文件加载当前版本（替代环境变量）"""
    try:
        with open('version_history.json', 'r') as f:
            data = json.load(f)
            return data['current_version']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return None

def update_version(version):
    """更新当前版本记录"""
    history = {
        "current_version": version,
        "last_checked": datetime.now().isoformat()
    }
    with open('version_history.json', 'w') as f:
        json.dump(history, f, indent=2)

def send_notification(new_version, release_info):
    """发送通知（在此示例中设置为输出，实际应发送邮件）"""
    print(f"::set-output name=has_update::true")
    print(f"::set-output name=new_version::{new_version}")
    
    # 在实际项目中，这里应该调用邮件发送API
    print(f"New version detected: {new_version}")

def main():
    # 获取当前存储的版本
    current_version = load_current_version()
    
    # 获取最新发布信息
    latest_release = get_latest_release()
    
    if not latest_release:
        print("Failed to fetch release information")
        return
    
    latest_version = latest_release['tag_name']
    
    print(f"Current version: {current_version}, Latest version: {latest_version}")
    
    # 如果是首次运行或版本不同
    if not current_version or current_version != latest_version:
        # 更新本地存储版本
        update_version(latest_version)
        
        # 发送通知
        send_notification(latest_version, latest_release)
    else:
        print("No new version available")
        print("::set-output name=has_update::false")

if __name__ == "__main__":
    main()

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
    """生成详细的邮件通知内容"""
    subject = f"New Release: {new_version} for {target_repo}"
    
    body = f"""
    <h2>New Release Detected: {new_version}</h2>
    <p>Repository: {target_repo}</p>
    <p>Release Name: {release_info.get('name', '')}</p>
    <p>Published at: {release_info['published_at']}</p>
    <p>Author: {release_info['author']['login']}</p>
    <hr>
    <h3>Release Notes:</h3>
    <div>{release_info.get('body', 'No release notes provided')}</div>
    <hr>
    <p><a href="{release_info['html_url']}">View on GitHub</a></p>
    """
    
    # 在实际项目中发送包含HTML格式的邮件
    print(f"::set-output name=release_body::{json.dumps(body)}")

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

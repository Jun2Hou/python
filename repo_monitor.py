import os
import json
import requests
from datetime import datetime

# 从环境变量获取配置
target_repo = os.environ['TARGET_REPO']
token = os.environ.get('GITHUB_TOKEN')

def get_latest_release():
    """获取目标仓库的最新发布版本"""
    url = f"https://api.github.com/repos/{target_repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching release: {e}")
        return None

def load_current_version():
    """从文件加载当前版本（避免使用环境变量）"""
    try:
        with open('version_history.json', 'r') as f:
            data = json.load(f)
            return data['current_version']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "v0.0.0"  # 默认初始版本

def update_version(new_version, release_info):
    """更新版本记录文件（仅在工作流脚本中调用）"""
    try:
        # 读取当前数据
        try:
            with open('version_history.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "current_version": "v0.0.0",
                "last_checked": datetime.utcnow().isoformat(),
                "version_history": []
            }
        
        # 添加新记录
        new_entry = {
            "version": new_version,
            "detected": datetime.utcnow().isoformat(),
            "release_info": {
                "url": release_info['html_url'],
                "name": release_info.get('name', ''),
                "published_at": release_info['published_at']
            }
        }
        
        # 更新主记录
        data['current_version'] = new_version
        data['last_checked'] = datetime.utcnow().isoformat()
        data['version_history'].append(new_entry)
        
        # 保存文件
        with open('version_history.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Updated version history to {new_version}")
        
    except Exception as e:
        print(f"Error updating version file: {e}")
        raise

def main():
    # 获取当前存储的版本
    current_version = load_current_version()
    
    # 获取最新发布信息
    latest_release = get_latest_release()
    
    if not latest_release:
        print("Failed to fetch release information")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')
        return
    
    latest_version = latest_release['tag_name']
    
    print(f"Current version: {current_version}, Latest version: {latest_version}")
    
    # 检查版本变化
    if current_version != latest_version:
        print(f"New version detected: {latest_version}")
        
        # 更新版本文件（不提交，由工作流处理）
        update_version(latest_version, latest_release)
        
        # 设置输出
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'has_update=true\n')
            f.write(f'new_version={latest_version}\n')
    else:
        print("No new version available")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')

if __name__ == "__main__":
    main()

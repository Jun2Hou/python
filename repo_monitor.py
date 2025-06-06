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
    """从文件加载当前版本"""
    try:
        with open('version_history.json', 'r') as f:
            data = json.load(f)
            return data['current_version']
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        # 第一次运行，创建新文件
        initial_data = {
            "current_version": "v0.0.0",
            "last_checked": datetime.utcnow().isoformat(),
            "version_history": []
        }
        with open('version_history.json', 'w') as f:
            json.dump(initial_data, f, indent=2)
        return "v0.0.0"

def update_version(new_version):
    """更新版本记录文件"""
    try:
        with open('version_history.json', 'r') as f:
            data = json.load(f)
            
        # 记录更新历史
        data['version_history'].append({
            "version": new_version,
            "detected": datetime.utcnow().isoformat()
        })
        
        # 更新当前版本
        data['current_version'] = new_version
        data['last_checked'] = datetime.utcnow().isoformat()
        
        with open('version_history.json', 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error updating version file: {e}")

def main():
    # 获取当前存储的版本
    current_version = load_current_version()
    
    # 获取最新发布信息
    latest_release = get_latest_release()
    
    if not latest_release:
        print("Failed to fetch release information")
        # 设置输出
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')
        return
    
    latest_version = latest_release['tag_name']
    
    print(f"Current version: {current_version}, Latest version: {latest_version}")
    
    # 如果是首次运行或版本不同
    if current_version != latest_version:
        print(f"New version detected: {latest_version}")
        update_version(latest_version)
        
        # 设置输出 (使用新的环境文件方式)
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'has_update=true\n')
            f.write(f'new_version={latest_version}\n')
    else:
        print("No new version available")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')

if __name__ == "__main__":
    main()

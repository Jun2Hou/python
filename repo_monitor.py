import os
import json
import requests
import sys
from datetime import datetime

# 从命令行参数获取安全仓库名称
safe_repo_name = sys.argv[1] if len(sys.argv) > 1 else "default"
target_repo = os.environ['TARGET_REPO']
token = os.environ.get('GITHUB_TOKEN')

# 为每个仓库创建单独的文件
VERSION_FILE = f"monitoring/version_history_{safe_repo_name}.json"
MONITORING_DIR = "monitoring"

def ensure_dir_exists():
    """确保监控目录存在"""
    if not os.path.exists(MONITORING_DIR):
        os.makedirs(MONITORING_DIR)

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
    """从仓库特定文件加载当前版本"""
    ensure_dir_exists()
    file_path = VERSION_FILE
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data['current_version']
        except (KeyError, json.JSONDecodeError):
            pass
    
    # 首次运行初始化文件
    init_data = {
        "current_version": "v0.0.0",
        "last_checked": datetime.utcnow().isoformat(),
        "version_history": []
    }
    with open(file_path, 'w') as f:
        json.dump(init_data, f, indent=2)
    
    return "v0.0.0"

def update_version(new_version, release_info):
    """更新仓库特定的版本文件"""
    ensure_dir_exists()
    file_path = VERSION_FILE
    
    # 加载或初始化数据
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {
            "current_version": "v0.0.0",
            "last_checked": datetime.utcnow().isoformat(),
            "version_history": []
        }
    
    # 添加新版本记录
    new_entry = {
        "version": new_version,
        "detected": datetime.utcnow().isoformat(),
        "release_info": {
            "url": release_info['html_url'],
            "name": release_info.get('name', ''),
            "published_at": release_info['published_at']
        }
    }
    
    # 更新数据
    data['current_version'] = new_version
    data['last_checked'] = datetime.utcnow().isoformat()
    data['version_history'].append(new_entry)
    
    # 保存文件
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated version history for {target_repo} to {new_version}")

def main():
    # 确保目录存在
    ensure_dir_exists()
    
    # 获取当前版本
    current_version = load_current_version()
    
    # 获取最新发布
    latest_release = get_latest_release()
    
    if not latest_release:
        print(f"Failed to fetch release information for {target_repo}")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')
        return
    
    latest_version = latest_release['tag_name']
    
    print(f"[{target_repo}] Current: {current_version}, Latest: {latest_version}")
    
    # 检查版本变化
    if current_version != latest_version:
        print(f"New version detected for {target_repo}: {latest_version}")
        
        # 更新版本文件
        update_version(latest_version, latest_release)
        
        # 设置输出
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'has_update=true\n')
            f.write(f'new_version={latest_version}\n')
    else:
        print(f"No new version for {target_repo}")
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write('has_update=false\n')

if __name__ == "__main__":
    main()

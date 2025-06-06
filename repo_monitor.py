import os
import json
import requests
import sys
from datetime import datetime
import logging

# 设置日志记录（只输出错误信息）
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

# 从命令行参数获取安全仓库名称
if len(sys.argv) > 1:
    safe_repo_name = sys.argv[1]
else:
    safe_repo_name = "default"
    
target_repo = os.environ['TARGET_REPO']
token = os.environ.get('GITHUB_TOKEN')
logger = logging.getLogger(__name__)

# 为每个仓库创建单独的文件
VERSION_FILE = f"version_history_{safe_repo_name}.json"
MONITORING_DIR = "."

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
        logger.error(f"Error fetching release: {e}")
        return None

def load_current_version():
    """从仓库特定文件加载当前版本"""
    ensure_dir_exists()
    file_path = VERSION_FILE
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return data.get('current_version', "v0.0.0")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading version file: {e}")
    
    # 首次运行初始化文件
    init_data = {
        "current_version": "v0.0.0",
        "last_checked": datetime.utcnow().isoformat(),
        "version_history": []
    }
    try:
        with open(file_path, 'w') as f:
            json.dump(init_data, f, indent=2)
    except Exception as e:
        logger.error(f"Error creating version file: {e}")
    
    return "v0.0.0"

def update_version(new_version, release_info):
    """更新仓库特定的版本文件"""
    ensure_dir_exists()
    file_path = VERSION_FILE
    
    # 加载或初始化数据
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {
                "current_version": "v0.0.0",
                "last_checked": datetime.utcnow().isoformat(),
                "version_history": []
            }
    except Exception as e:
        logger.error(f"Error loading version data: {e}")
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
    data['version_history'].insert(0, new_entry)  # 插入到开头
    
    # 保存文件
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving version file: {e}")
        return False

def main():
    # 确保目录存在
    ensure_dir_exists()
    
    # 获取当前版本
    current_version = load_current_version()
    
    # 获取最新发布
    latest_release = get_latest_release()
    
    if not latest_release:
        # 错误时输出空字符串
        print("")
        return 1
    
    latest_version = latest_release['tag_name']
    
    # 检查版本变化
    if current_version != latest_version:
        # 更新版本文件
        if update_version(latest_version, latest_release):
            # 成功更新时输出版本号（只包含版本号）
            print(latest_version)
            return 0
        else:
            # 文件更新失败时输出空字符串
            print("")
            return 1
    else:
        # 没有新版本时输出空字符串
        print("")
        return 0

if __name__ == "__main__":
    exit(main())

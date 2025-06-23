import os
import json
import requests
import sys
from datetime import datetime
import logging
import re

# 配置日志记录器（只记录错误信息到 stderr）
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

# 从命令行参数获取安全仓库名称
if len(sys.argv) > 1:
    safe_repo_name = sys.argv[1]
else:
    safe_repo_name = "default"
    
target_repo = os.environ['TARGET_REPO']
token = os.environ.get('GITHUB_TOKEN')

# 版本文件路径
VERSION_FILE = f"version_history_{safe_repo_name}.json"

def get_latest_release():
    """获取目标仓库的最新发布版本"""
    url = f"https://api.github.com/repos/{target_repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching release: {e}")
        return None

def load_current_version():
    """从文件加载当前版本"""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('current_version', "v0.0.0")
    except Exception as e:
        logger.error(f"Error loading version file: {e}")
    
    # 如果文件不存在或读取失败，返回默认值
    return "v0.0.0"

def update_version(new_version, release_info):
    """更新版本文件"""
    try:
        # 尝试加载现有数据
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
        else:
            # 初始化数据
            data = {
                "current_version": "v0.0.0",
                "last_checked": datetime.utcnow().isoformat(),
                "version_history": []
            }
        
        # 创建新版本记录
        new_entry = {
            "version": new_version,
            "detected": datetime.utcnow().isoformat(),
            "release_info": {
                "url": release_info['html_url'],
                "name": release_info.get('name', ''),
                "published_at": release_info['published_at']
            }
        }
        
        # 更新数据结构
        data['current_version'] = new_version
        data['last_checked'] = datetime.utcnow().isoformat()
        data['version_history'].insert(0, new_entry)  # 插入到开头
        
        # 保存文件
        with open(VERSION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 只在stderr记录更新消息
        logger.info(f"Updated version history for {target_repo} to {new_version}")
        return True
    except Exception as e:
        logger.error(f"Error updating version file: {e}")
        return False

def main():
    # 获取当前版本
    current_version = load_current_version()
    
    # 获取最新发布
    latest_release = get_latest_release()
    
    if not latest_release:
        # 错误时输出空字符串（标准输出）
        return ""
    
    latest_version = latest_release['tag_name']
    
    # 标准化版本号格式
    if latest_version.startswith('v'):
        cleaned_version = latest_version[1:]
    else:
        cleaned_version = latest_version
    
    # 验证版本号格式
    if not re.match(r'^\d+\.\d+\.\d+$', cleaned_version):
        logger.error(f"Invalid version format: {cleaned_version}")
        return ""
    
    # 检查版本变化
    if current_version != cleaned_version:
        # 更新版本文件
        if update_version(cleaned_version, latest_release):
            # 成功更新时输出标准化的版本号
            print(cleaned_version)
            return cleaned_version
        else:
            # 文件更新失败时输出空字符串
            return ""
    else:
        # 没有新版本时输出空字符串
        return ""

if __name__ == "__main__":
    # 只输出版本号（标准输出）或空字符串
    result = main()
    print(result)

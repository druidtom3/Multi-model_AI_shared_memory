#!/usr/bin/env python3
"""
多AI協作開發平台啟動腳本

簡潔的啟動腳本，遵循Linus原則：
- 自動檢查環境
- 清晰的錯誤提示
- 簡單的啟動流程
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# 設置基本日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """檢查Python版本"""
    if sys.version_info < (3, 8):
        logger.error("需要Python 3.8或更高版本")
        logger.error(f"當前版本: {sys.version}")
        return False
    return True

def check_dependencies():
    """檢查必要的依賴套件"""
    required_packages = [
        'flask',
        'requests', 
        'aiohttp',
        'pyyaml',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error("缺少必要的依賴套件:")
        for package in missing_packages:
            logger.error(f"  - {package}")
        logger.error("請執行: pip install -r requirements.txt")
        return False
    
    return True

def check_project_structure():
    """檢查專案結構"""
    required_dirs = [
        'src/core',
        'src/ai_services', 
        'src/web',
        'src/web/templates',
        'data',
        'configs',
        'workspace'
    ]
    
    required_files = [
        'src/core/ai_coordinator.py',
        'src/core/role_system.py',
        'src/core/event_recorder.py',
        'src/ai_services/api_clients.py',
        'src/web/app.py',
        'configs/ai_providers.yaml',
        'configs/roles.yaml'
    ]
    
    project_root = Path(__file__).parent
    
    # 檢查目錄
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.error(f"缺少目錄: {dir_path}")
            return False
    
    # 檢查檔案
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.error(f"缺少檔案: {file_path}")
            return False
    
    return True

def check_environment_config():
    """檢查環境配置"""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    
    if not env_file.exists():
        logger.warning(".env 檔案不存在")
        logger.info("正在從 .env.example 創建 .env 檔案...")
        
        env_example = project_root / '.env.example'
        if env_example.exists():
            try:
                import shutil
                shutil.copy(env_example, env_file)
                logger.info("已創建 .env 檔案，請編輯並設置API金鑰")
            except Exception as e:
                logger.error(f"創建 .env 檔案失敗: {e}")
                return False
        else:
            logger.error("找不到 .env.example 檔案")
            return False
    
    # 檢查是否至少設置了一個API金鑰
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    api_keys = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY', 
        'XAI_API_KEY',
        'GOOGLE_AI_KEY'
    ]
    
    configured_keys = []
    for key in api_keys:
        value = os.getenv(key)
        if value and value.strip() and value != f'your_{key.lower()}_here':
            configured_keys.append(key)
    
    if not configured_keys:
        logger.warning("未檢測到任何已配置的API金鑰")
        logger.warning("平台仍可啟動，但AI功能將無法使用")
        logger.info("請編輯 .env 檔案並設置至少一個AI供應商的API金鑰:")
        for key in api_keys:
            logger.info(f"  - {key}")
        
        user_input = input("\n是否繼續啟動？(y/N): ").strip().lower()
        if user_input != 'y':
            return False
    else:
        logger.info(f"已配置 {len(configured_keys)} 個API金鑰")
    
    return True

def check_ports():
    """檢查埠口可用性"""
    import socket
    
    host = os.getenv('WEB_HOST', '127.0.0.1')
    port = int(os.getenv('WEB_PORT', 5000))
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        logger.info(f"埠口 {host}:{port} 可用")
        return True
    except OSError:
        logger.error(f"埠口 {host}:{port} 已被占用")
        logger.error("請修改 .env 檔案中的 WEB_PORT 設置")
        return False

def run_system_checks():
    """執行所有系統檢查"""
    logger.info("=== 多AI協作開發平台啟動檢查 ===")
    
    checks = [
        ("Python版本", check_python_version),
        ("依賴套件", check_dependencies),
        ("專案結構", check_project_structure), 
        ("環境配置", check_environment_config),
        ("埠口可用性", check_ports)
    ]
    
    for check_name, check_func in checks:
        logger.info(f"檢查 {check_name}...")
        if not check_func():
            logger.error(f"❌ {check_name} 檢查失敗")
            return False
        else:
            logger.info(f"✅ {check_name} 檢查通過")
    
    logger.info("=== 所有檢查都通過！ ===")
    return True

def start_application():
    """啟動應用程式"""
    try:
        # 設置Python路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 載入環境變數
        from dotenv import load_dotenv
        load_dotenv()
        
        # 導入並啟動Flask應用
        logger.info("正在啟動Web應用...")
        
        from src.web.app import run_app
        run_app()
        
    except KeyboardInterrupt:
        logger.info("\n應用程式已停止")
    except Exception as e:
        logger.error(f"啟動失敗: {e}")
        logger.error("請檢查日誌檔案以獲取更多詳細資訊")
        return False
    
    return True

def main():
    """主函數"""
    print("🚀 多AI協作開發平台")
    print("基於Linus工程哲學的簡潔AI協作平台\n")
    
    try:
        # 執行系統檢查
        if not run_system_checks():
            print("\n❌ 系統檢查失敗，無法啟動")
            print("請根據上述錯誤訊息進行修正")
            sys.exit(1)
        
        print("\n🎉 系統檢查完成，準備啟動...")
        
        # 顯示啟動資訊
        host = os.getenv('WEB_HOST', '127.0.0.1')
        port = os.getenv('WEB_PORT', '5000')
        
        print(f"\n📡 Web界面將在以下地址啟動:")
        print(f"   http://{host}:{port}")
        print(f"\n💡 使用說明:")
        print(f"   1. 在瀏覽器中訪問上述地址")
        print(f"   2. 在「AI聊天」頁面選擇AI配置")
        print(f"   3. 開始與AI協作開發")
        print(f"\n🔧 Linus原則提醒:")
        print(f"   - 保持設計簡潔")
        print(f"   - 消除特殊情況") 
        print(f"   - 解決真實問題")
        print(f"   - 維持向後相容")
        
        print(f"\n🚀 正在啟動...")
        print("=" * 50)
        
        # 啟動應用
        if not start_application():
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"啟動腳本執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
系統測試腳本 - 修復版本
"""

import sys
import logging
import os
from pathlib import Path

# 設置編碼以避免Windows中文問題
os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """測試基本模組導入"""
    print("Testing module imports...")
    
    try:
        # 設置路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        
        # 添加到Python路徑
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 測試導入核心模組
        from core.ai_coordinator import AICoordinator
        from core.role_system import RoleSystem
        from core.event_recorder import EventRecorder
        from ai_services.api_clients import AIAPIClients
        
        print("=> Module imports successful")
        return True
        
    except Exception as e:
        print(f"=> Module import failed: {e}")
        return False

def test_role_system_basic():
    """測試角色系統基本功能"""
    print("Testing role system...")
    
    try:
        # 重新設置路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            
        from core.role_system import RoleSystem
        
        configs_path = Path(__file__).parent / "configs"
        role_system = RoleSystem(configs_path)
        
        # 基本功能測試
        programming_roles = role_system.get_available_roles(True, False)
        non_programming_roles = role_system.get_available_roles(False, True)
        
        print(f"=> Programming roles: {len(programming_roles)}")
        print(f"=> General roles: {len(non_programming_roles)}")
        return True
        
    except Exception as e:
        print(f"=> Role system test failed: {e}")
        return False

def test_event_recorder_basic():
    """測試事件記錄基本功能"""
    print("Testing event recorder...")
    
    try:
        # 重新設置路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            
        from core.event_recorder import EventRecorder
        
        test_data_path = Path(__file__).parent / "test_data"
        test_data_path.mkdir(exist_ok=True)
        
        recorder = EventRecorder(test_data_path)
        
        # 測試基本記錄
        test_report = {
            'ai_config': {'provider': 'test', 'model': 'test', 'role': 'test'},
            'user_message': 'Test message',
            'ai_response': 'Test response',
            'processing_status': 'success'
        }
        
        recorder.append_work_report(test_report)
        
        recent_events = recorder.get_recent_events(limit=1)
        print(f"=> Event recording successful, events: {len(recent_events)}")
        return True
        
    except Exception as e:
        print(f"=> Event recorder test failed: {e}")
        return False

def test_api_clients_basic():
    """測試API客戶端基本功能"""
    print("Testing API clients...")
    
    try:
        # 重新設置路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            
        from ai_services.api_clients import SyncAIAPIClients
        
        client = SyncAIAPIClients()
        api_status = client.check_api_keys()
        
        available = client.get_available_providers()
        print(f"=> API key check completed")
        print(f"=> Available providers: {available}")
        return True
        
    except Exception as e:
        print(f"=> API client test failed: {e}")
        return False

def test_files_exist():
    """測試重要檔案是否存在"""
    print("Checking file structure...")
    
    project_root = Path(__file__).parent
    
    required_files = [
        "src/core/ai_coordinator.py",
        "src/core/role_system.py", 
        "src/core/event_recorder.py",
        "src/ai_services/api_clients.py",
        "src/web/app.py",
        "configs/ai_providers.yaml",
        "configs/roles.yaml",
        "requirements.txt"
    ]
    
    missing = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"=> Missing files: {missing}")
        return False
    else:
        print(f"=> Checked {len(required_files)} files, all exist")
        return True

def main():
    print("Multi-AI Collaboration Platform - System Test")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_files_exist),
        ("Module Imports", test_basic_imports),
        ("Role System", test_role_system_basic),
        ("Event Recorder", test_event_recorder_basic),
        ("API Clients", test_api_clients_basic)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if test_func():
                passed += 1
                print(f"=> {test_name}: PASSED")
            else:
                failed += 1
                print(f"=> {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"=> {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 40)
    print(f"Results: PASSED {passed}/{passed + failed}")
    
    if failed == 0:
        print("=> All tests passed! System ready to start")
        print("=> You can run: python start.py")
        return True
    else:
        print(f"=> {failed} tests failed, please check errors")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
簡化版系統測試腳本 - 避免編碼問題
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """測試基本模組導入"""
    print("測試模組導入...")
    
    try:
        # 設置路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        sys.path.insert(0, str(src_path))
        
        # 測試導入
        from core.ai_coordinator import AICoordinator
        from core.role_system import RoleSystem
        from core.event_recorder import EventRecorder
        from ai_services.api_clients import AIAPIClients
        
        print("=> 模組導入成功")
        return True
        
    except Exception as e:
        print(f"=> 模組導入失敗: {e}")
        return False

def test_role_system_basic():
    """測試角色系統基本功能"""
    print("測試角色系統...")
    
    try:
        from core.role_system import RoleSystem
        
        configs_path = Path(__file__).parent / "configs"
        role_system = RoleSystem(configs_path)
        
        # 基本功能測試
        programming_roles = role_system.get_available_roles(True, False)
        non_programming_roles = role_system.get_available_roles(False, True)
        
        print(f"=> 程式類角色: {len(programming_roles)}")
        print(f"=> 一般角色: {len(non_programming_roles)}")
        return True
        
    except Exception as e:
        print(f"=> 角色系統測試失敗: {e}")
        return False

def test_event_recorder_basic():
    """測試事件記錄基本功能"""
    print("測試事件記錄...")
    
    try:
        from core.event_recorder import EventRecorder
        
        test_data_path = Path(__file__).parent / "test_data"
        test_data_path.mkdir(exist_ok=True)
        
        recorder = EventRecorder(test_data_path)
        
        # 測試基本記錄
        test_report = {
            'ai_config': {'provider': 'test', 'model': 'test', 'role': 'test'},
            'user_message': '測試',
            'ai_response': '測試回應',
            'processing_status': 'success'
        }
        
        recorder.append_work_report(test_report)
        
        recent_events = recorder.get_recent_events(limit=1)
        print(f"=> 事件記錄成功，事件數: {len(recent_events)}")
        return True
        
    except Exception as e:
        print(f"=> 事件記錄測試失敗: {e}")
        return False

def test_api_clients_basic():
    """測試API客戶端基本功能"""
    print("測試API客戶端...")
    
    try:
        from ai_services.api_clients import SyncAIAPIClients
        
        client = SyncAIAPIClients()
        api_status = client.check_api_keys()
        
        available = client.get_available_providers()
        print(f"=> API金鑰檢查完成")
        print(f"=> 可用供應商: {available}")
        return True
        
    except Exception as e:
        print(f"=> API客戶端測試失敗: {e}")
        return False

def test_files_exist():
    """測試重要檔案是否存在"""
    print("檢查檔案結構...")
    
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
        print(f"=> 缺少檔案: {missing}")
        return False
    else:
        print(f"=> 檢查了 {len(required_files)} 個檔案，都存在")
        return True

def main():
    print("多AI協作開發平台 - 系統測試")
    print("=" * 40)
    
    tests = [
        ("檔案結構", test_files_exist),
        ("模組導入", test_basic_imports),
        ("角色系統", test_role_system_basic),
        ("事件記錄", test_event_recorder_basic),
        ("API客戶端", test_api_clients_basic)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if test_func():
                passed += 1
                print(f"=> {test_name}: 通過")
            else:
                failed += 1
                print(f"=> {test_name}: 失敗")
        except Exception as e:
            failed += 1
            print(f"=> {test_name}: 異常 - {e}")
    
    print("\n" + "=" * 40)
    print(f"結果: 通過 {passed}/{passed + failed}")
    
    if failed == 0:
        print("=> 系統測試通過！可以啟動平台")
        return True
    else:
        print("=> 有測試失敗，請檢查錯誤")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
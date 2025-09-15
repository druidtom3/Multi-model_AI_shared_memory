#!/usr/bin/env python3
"""
系統功能測試腳本

簡潔的測試腳本，驗證核心功能：
- 核心模組導入
- 角色系統功能
- 事件記錄功能  
- API客戶端基礎功能
"""

import sys
import json
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """測試核心模組導入"""
    logger.info("測試模組導入...")
    
    try:
        # 設置Python路徑
        project_root = Path(__file__).parent
        src_path = project_root / 'src'
        sys.path.insert(0, str(src_path))
        
        # 測試導入核心模組
        from core.ai_coordinator import AICoordinator, SyncAICoordinator
        from core.role_system import RoleSystem
        from core.event_recorder import EventRecorder
        from ai_services.api_clients import AIAPIClients, SyncAIAPIClients
        
        logger.info("OK 所有核心模組導入成功")
        return True
        
    except ImportError as e:
        logger.error(f"XX 模組導入失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"XX 導入測試錯誤: {e}")
        return False

def test_role_system():
    """測試角色系統"""
    logger.info("測試角色系統...")
    
    try:
        from core.role_system import RoleSystem
        
        # 創建角色系統實例
        configs_path = Path(__file__).parent / "configs"
        role_system = RoleSystem(configs_path)
        
        # 測試獲取可用角色
        programming_roles = role_system.get_available_roles(True, False)
        non_programming_roles = role_system.get_available_roles(False, True)
        
        logger.info(f"程式類角色數量: {len(programming_roles)}")
        logger.info(f"一般助理角色數量: {len(non_programming_roles)}")
        
        # 測試角色驗證
        validation = role_system.validate_role_assignment('system_design', 'system_architect')
        logger.info(f"角色分配驗證: {validation['is_suitable']}")
        
        # 測試prompt建構
        prompt = role_system.build_role_prompt(
            'anthropic', 
            'claude-3-5-sonnet-20241022', 
            'system_architect',
            {'session_id': 'test123'}
        )
        
        logger.info(f"Prompt長度: {len(prompt)} 字符")
        logger.info("✅ 角色系統測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 角色系統測試失敗: {e}")
        return False

def test_event_recorder():
    """測試事件記錄系統"""
    logger.info("測試事件記錄系統...")
    
    try:
        from core.event_recorder import EventRecorder
        
        # 創建測試資料夾
        test_data_path = Path(__file__).parent / "test_data"
        test_data_path.mkdir(exist_ok=True)
        
        # 創建事件記錄器
        recorder = EventRecorder(test_data_path)
        
        # 測試記錄工作報告
        test_report = {
            'ai_config': {
                'provider': 'anthropic', 
                'model': 'claude-3-5-sonnet-20241022', 
                'role': 'system_architect'
            },
            'user_message': '測試用戶訊息',
            'ai_response': '測試AI回應',
            'processing_status': 'success'
        }
        
        recorder.append_work_report(test_report)
        logger.info("工作報告記錄成功")
        
        # 測試AI切換記錄
        recorder.append_ai_handover(
            {'provider': 'anthropic', 'role': 'system_architect'},
            {'provider': 'openai', 'role': 'coder_programmer'}, 
            '測試切換',
            {'session_id': 'test123'}
        )
        logger.info("AI切換記錄成功")
        
        # 測試事件查詢
        recent_events = recorder.get_recent_events(limit=5)
        logger.info(f"最近事件數量: {len(recent_events)}")
        
        # 測試專案狀態重建
        state = recorder.rebuild_project_state()
        logger.info(f"專案狀態事件數: {state.get('total_events', 0)}")
        
        logger.info("✅ 事件記錄系統測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 事件記錄系統測試失敗: {e}")
        return False

def test_api_clients():
    """測試API客戶端"""
    logger.info("測試API客戶端...")
    
    try:
        from ai_services.api_clients import SyncAIAPIClients
        
        # 創建API客戶端
        client = SyncAIAPIClients()
        
        # 測試API金鑰檢查
        api_status = client.check_api_keys()
        logger.info("API金鑰狀態:")
        for provider, configured in api_status.items():
            status = "✅ 已配置" if configured else "❌ 未配置"
            logger.info(f"  {provider}: {status}")
        
        # 測試獲取可用供應商
        available = client.get_available_providers()
        logger.info(f"可用AI供應商: {available}")
        
        logger.info("✅ API客戶端測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ API客戶端測試失敗: {e}")
        return False

def test_ai_coordinator():
    """測試AI協調器"""
    logger.info("測試AI協調器...")
    
    try:
        from core.ai_coordinator import SyncAICoordinator
        
        # 創建測試工作區
        test_workspace = Path(__file__).parent / "test_workspace"
        test_workspace.mkdir(exist_ok=True)
        
        # 創建協調器
        coordinator = SyncAICoordinator(str(test_workspace))
        
        # 測試獲取專案狀態
        status = coordinator.get_project_status()
        logger.info(f"專案路徑: {status.get('project_path')}")
        logger.info(f"會話ID: {status.get('session_id')}")
        
        # 測試子系統狀態
        subsystems = status.get('subsystems_status', {})
        for system, status_ok in subsystems.items():
            status_str = "✅ 正常" if status_ok else "❌ 未啟用"
            logger.info(f"  {system}: {status_str}")
        
        logger.info("✅ AI協調器測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI協調器測試失敗: {e}")
        return False

def test_configuration_files():
    """測試配置檔案"""
    logger.info("測試配置檔案...")
    
    try:
        import yaml
        
        project_root = Path(__file__).parent
        
        # 測試AI供應商配置
        providers_file = project_root / "configs" / "ai_providers.yaml"
        if providers_file.exists():
            with open(providers_file, 'r', encoding='utf-8') as f:
                providers_config = yaml.safe_load(f)
            
            providers = providers_config.get('providers', {})
            logger.info(f"配置的AI供應商數量: {len(providers)}")
            
            for provider, config in providers.items():
                models = config.get('models', {})
                logger.info(f"  {provider}: {len(models)} 個模型")
        else:
            logger.warning("AI供應商配置檔案不存在")
        
        # 測試角色配置
        roles_file = project_root / "configs" / "roles.yaml" 
        if roles_file.exists():
            with open(roles_file, 'r', encoding='utf-8') as f:
                roles_config = yaml.safe_load(f)
            
            prog_roles = roles_config.get('programming_roles', {})
            non_prog_roles = roles_config.get('non_programming_roles', {})
            
            logger.info(f"程式類角色: {len(prog_roles)} 個")
            logger.info(f"一般助理角色: {len(non_prog_roles)} 個")
        else:
            logger.warning("角色配置檔案不存在")
        
        logger.info("✅ 配置檔案測試通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置檔案測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("多AI協作開發平台系統測試")
    print("=" * 40)
    
    tests = [
        ("模組導入", test_imports),
        ("配置檔案", test_configuration_files),
        ("角色系統", test_role_system),
        ("事件記錄系統", test_event_recorder),
        ("API客戶端", test_api_clients), 
        ("AI協調器", test_ai_coordinator)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n>> 執行 {test_name} 測試...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"XX {test_name} 測試異常: {e}")
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"測試結果:")
    print(f"   通過: {passed}")
    print(f"   失敗: {failed}")
    print(f"   成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n>> 所有測試都通過！系統已準備就緒。")
        print(">> 可以執行 python start.py 啟動平台")
        return True
    else:
        print(f"\n>> 有 {failed} 個測試失敗，請檢查上述錯誤訊息")
        print("建議:")
        print("   1. 檢查Python依賴是否完整安裝")
        print("   2. 確認專案檔案結構完整") 
        print("   3. 檢查配置檔案格式")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
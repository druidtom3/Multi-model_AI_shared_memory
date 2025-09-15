"""
AI協調器 - 多AI協作開發平台的核心組件

基於 Linus 工程哲學設計：
- 簡潔性優先：統一的AI對話介面
- 好品味：讓特殊情況消失
- 實用主義：解決真實問題，避免過度設計
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class AICoordinator:
    """
    核心AI協調器
    
    職責：
    1. 統一的AI對話介面
    2. 角色系統集成
    3. 事件流記錄協調
    4. 錯誤處理和降級
    """
    
    def __init__(self, project_path: str = None):
        """初始化協調器，載入必要配置"""
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.workspace_path = self.project_path / "workspace"
        self.data_path = self.project_path / "data"
        self.configs_path = self.project_path / "configs"
        
        # 確保必要目錄存在
        self._ensure_directories()
        
        # 初始化子系統
        self.role_system = None  # 延遲初始化
        self.event_recorder = None  # 延遲初始化
        self.api_clients = None  # 延遲初始化
        
        # 當前會話狀態
        self.current_ai_config = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 設置日誌
        self._setup_logging()
        
        logger.info(f"AICoordinator initialized for project: {self.project_path}")
    
    def _ensure_directories(self):
        """確保必要的目錄存在"""
        for path in [self.workspace_path, self.data_path, self.configs_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """設置日誌系統"""
        log_file = self.data_path / "ai_coordinator.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        global logger
        logger = logging.getLogger(__name__)
    
    def _lazy_init_subsystems(self):
        """延遲初始化子系統（遵循簡潔原則：只在需要時載入）"""
        if self.role_system is None:
            try:
                from .role_system import RoleSystem
                self.role_system = RoleSystem(self.configs_path)
            except ImportError:
                logger.warning("RoleSystem not available, using basic mode")
                self.role_system = None
        
        if self.event_recorder is None:
            try:
                from .event_recorder import EventRecorder
                self.event_recorder = EventRecorder(self.data_path)
            except ImportError:
                logger.warning("EventRecorder not available, events won't be persisted")
                self.event_recorder = None
        
        if self.api_clients is None:
            try:
                from ..ai_services.api_clients import AIAPIClients
                self.api_clients = AIAPIClients()
            except ImportError:
                logger.error("AI API clients not available")
                self.api_clients = None
    
    async def chat_with_ai(self, ai_config: Dict[str, str], message: str, 
                          custom_role: str = None) -> Dict[str, Any]:
        """
        統一AI對話介面
        
        Args:
            ai_config: {'provider': 'anthropic', 'model': 'claude-3-5-sonnet-20241022', 'role': 'system_architect'}
            message: 使用者訊息
            custom_role: 自訂角色prompt（可選）
            
        Returns:
            Dict包含AI回應和處理結果
        """
        try:
            self._lazy_init_subsystems()
            
            # 記錄對話開始
            logger.info(f"Starting conversation with {ai_config}")
            
            # 建構角色prompt
            system_prompt = self._build_system_prompt(ai_config, custom_role)
            
            # 調用AI API
            ai_response = await self._call_ai_api(ai_config, message, system_prompt)
            
            # 更新當前配置
            self.current_ai_config = ai_config
            
            # 處理和記錄回應
            result = await self._process_ai_response(message, ai_response, ai_config)
            
            logger.info("Conversation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in chat_with_ai: {str(e)}")
            return self._error_response(str(e), ai_config)
    
    def _build_system_prompt(self, ai_config: Dict[str, str], custom_role: str = None) -> str:
        """建構系統prompt"""
        if self.role_system:
            return self.role_system.build_role_prompt(
                ai_config['provider'], 
                ai_config['model'], 
                ai_config['role'],
                self._get_project_context(),
                custom_role
            )
        else:
            # 基本模式：簡單的角色描述
            base_prompt = f"你是一個{ai_config.get('role', 'assistant')}，專注於高品質的軟體開發。"
            
            # 如果是程式類角色，強制加入Linus原則
            programming_roles = ['system_architect', 'coder_programmer', 'coder_reviewer', 
                               'devops_engineer', 'qa_engineer', 'performance_optimizer', 'technical_writer']
            
            if ai_config.get('role') in programming_roles:
                base_prompt += """
                
請嚴格遵循Linus工程哲學：
1. 好品味：讓特殊情況消失，統一處理方式
2. 簡潔性：避免不必要的複雜度，縮排不超過3層
3. 實用主義：解決真實問題，避免過度設計
4. Never break userspace：保持向後相容性
                """
            
            return base_prompt + (f"\n\n{custom_role}" if custom_role else "")
    
    async def _call_ai_api(self, ai_config: Dict[str, str], message: str, system_prompt: str) -> str:
        """調用AI API"""
        if not self.api_clients:
            raise Exception("AI API clients not available")
        
        provider = ai_config['provider']
        model = ai_config['model']
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # 根據提供商調用相應API
        if provider == 'openai':
            return await self.api_clients.call_openai(model, messages)
        elif provider == 'anthropic':
            return await self.api_clients.call_anthropic(model, messages)
        elif provider == 'xai':
            return await self.api_clients.call_xai(model, messages)
        elif provider == 'google':
            return await self.api_clients.call_google(model, messages)
        else:
            raise Exception(f"Unsupported AI provider: {provider}")
    
    async def _process_ai_response(self, user_message: str, ai_response: str, 
                                 ai_config: Dict[str, str]) -> Dict[str, Any]:
        """處理AI回應，提取工作報告並記錄事件"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'ai_config': ai_config,
            'user_message': user_message,
            'ai_response': ai_response,
            'processing_status': 'success'
        }
        
        try:
            # 嘗試提取結構化工作報告
            if self._is_programming_role(ai_config.get('role')):
                work_report = await self._extract_work_report(user_message, ai_response, ai_config)
                if work_report:
                    result['work_report'] = work_report
                    result['linus_compliance'] = self._check_linus_compliance(work_report, ai_config)
            
            # 記錄到事件流
            if self.event_recorder:
                self.event_recorder.append_work_report(result)
            
        except Exception as e:
            logger.warning(f"Error processing AI response: {str(e)}")
            result['processing_status'] = 'partial_failure'
            result['processing_error'] = str(e)
        
        return result
    
    def _is_programming_role(self, role: str) -> bool:
        """檢查是否為程式類角色"""
        programming_roles = [
            'system_architect', 'coder_programmer', 'coder_reviewer',
            'devops_engineer', 'qa_engineer', 'performance_optimizer', 'technical_writer'
        ]
        return role in programming_roles
    
    async def _extract_work_report(self, user_message: str, ai_response: str, 
                                 ai_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """提取結構化工作報告（簡化版本）"""
        # 這裡實作簡單的關鍵詞提取，後續會被report_extractor取代
        try:
            # 簡單的關鍵詞檢測
            report = {
                'task_type': self._detect_task_type(ai_response),
                'summary': ai_response[:200] + '...' if len(ai_response) > 200 else ai_response,
                'extraction_method': 'simple_keyword',
                'confidence': 'low'
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error extracting work report: {str(e)}")
            return None
    
    def _detect_task_type(self, response: str) -> str:
        """簡單的任務類型檢測"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['架構', '設計', 'architecture', 'design']):
            return 'system_design'
        elif any(word in response_lower for word in ['實作', '程式碼', 'code', 'implement']):
            return 'feature_dev'
        elif any(word in response_lower for word in ['修復', 'bug', 'fix', 'error']):
            return 'bug_fix'
        elif any(word in response_lower for word in ['審查', 'review', '檢查']):
            return 'code_review'
        elif any(word in response_lower for word in ['測試', 'test', 'testing']):
            return 'testing'
        elif any(word in response_lower for word in ['文檔', 'document', 'documentation']):
            return 'documentation'
        else:
            return 'general'
    
    def _check_linus_compliance(self, work_report: Dict[str, Any], 
                              ai_config: Dict[str, str]) -> Dict[str, Any]:
        """檢查Linus原則合規性（基本版本）"""
        # 基本的合規性檢查
        compliance = {
            'checked': True,
            'score': 'unknown',
            'method': 'basic_check',
            'violations': [],
            'good_aspects': []
        }
        
        # 這裡會被專門的合規檢查器取代
        return compliance
    
    def _get_project_context(self) -> Dict[str, Any]:
        """獲取專案上下文"""
        context = {
            'project_path': str(self.project_path),
            'workspace_path': str(self.workspace_path),
            'session_id': self.session_id,
            'current_ai': self.current_ai_config
        }
        
        # 如果有事件記錄器，添加最近的事件
        if self.event_recorder:
            try:
                recent_events = self.event_recorder.get_recent_events(limit=5)
                context['recent_events'] = recent_events
            except:
                pass
        
        return context
    
    def switch_ai_role(self, new_ai_config: Dict[str, str], 
                      handover_context: str = None) -> Dict[str, Any]:
        """AI角色切換，處理交接context"""
        try:
            old_config = self.current_ai_config
            self.current_ai_config = new_ai_config
            
            # 記錄角色切換事件
            if self.event_recorder:
                self.event_recorder.append_ai_handover(
                    from_ai=old_config,
                    to_ai=new_ai_config,
                    reason=handover_context or "User requested role switch",
                    context=self._get_project_context()
                )
            
            logger.info(f"Switched from {old_config} to {new_ai_config}")
            
            return {
                'status': 'success',
                'from_config': old_config,
                'to_config': new_ai_config,
                'handover_context': handover_context
            }
            
        except Exception as e:
            logger.error(f"Error switching AI role: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def get_project_status(self) -> Dict[str, Any]:
        """獲取當前專案狀態摘要"""
        try:
            status = {
                'project_path': str(self.project_path),
                'session_id': self.session_id,
                'current_ai_config': self.current_ai_config,
                'timestamp': datetime.now().isoformat(),
                'subsystems_status': {
                    'role_system': self.role_system is not None,
                    'event_recorder': self.event_recorder is not None,
                    'api_clients': self.api_clients is not None
                }
            }
            
            # 添加最近的活動摘要
            if self.event_recorder:
                try:
                    recent_events = self.event_recorder.get_recent_events(limit=10)
                    status['recent_activity'] = {
                        'total_events': len(recent_events),
                        'event_types': list(set([e.get('type', 'unknown') for e in recent_events]))
                    }
                except:
                    pass
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting project status: {str(e)}")
            return {'error': str(e)}
    
    def validate_linus_compliance(self, work_report: Dict[str, Any]) -> Dict[str, Any]:
        """檢查工作報告是否符合Linus原則"""
        # 這個方法會在後續被專門的合規檢查器強化
        return self._check_linus_compliance(work_report, self.current_ai_config or {})
    
    def _error_response(self, error_message: str, ai_config: Dict[str, str]) -> Dict[str, Any]:
        """生成錯誤回應"""
        return {
            'timestamp': datetime.now().isoformat(),
            'ai_config': ai_config,
            'status': 'error',
            'error': error_message,
            'processing_status': 'failed'
        }


# 簡單的同步包裝器，方便測試
class SyncAICoordinator:
    """同步版本的AI協調器，便於測試和簡單使用"""
    
    def __init__(self, project_path: str = None):
        self.async_coordinator = AICoordinator(project_path)
    
    def chat_with_ai(self, ai_config: Dict[str, str], message: str, 
                    custom_role: str = None) -> Dict[str, Any]:
        """同步版本的AI對話"""
        import asyncio
        return asyncio.run(
            self.async_coordinator.chat_with_ai(ai_config, message, custom_role)
        )
    
    def get_project_status(self) -> Dict[str, Any]:
        """獲取專案狀態"""
        return self.async_coordinator.get_project_status()
    
    def switch_ai_role(self, new_ai_config: Dict[str, str], 
                      handover_context: str = None) -> Dict[str, Any]:
        """切換AI角色"""
        return self.async_coordinator.switch_ai_role(new_ai_config, handover_context)


if __name__ == "__main__":
    # 簡單測試
    coordinator = SyncAICoordinator("./test_project")
    status = coordinator.get_project_status()
    print(f"Project status: {json.dumps(status, indent=2, ensure_ascii=False)}")
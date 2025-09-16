"""
事件流記錄系統 - 專案歷史和狀態管理

基於 Linus 工程哲學設計：
- 統一的事件記錄格式（好品味原則）
- 檔案系統作為唯一真相來源
- 簡潔的查詢和重建機制
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


class EventRecorder:
    """
    事件流記錄系統
    
    職責：
    1. 統一事件格式記錄
    2. 事件查詢和檢索
    3. 專案狀態重建
    4. 事件流備份和恢復
    """
    
    def __init__(self, data_path: Path):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 事件流檔案
        self.events_file = self.data_path / "project_events.json"
        self.backup_dir = self.data_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 事件類型定義
        self.event_types = {
            "work_report": "AI完整工作報告",
            "file_change": "檔案系統變更", 
            "ai_handover": "AI切換交接",
            "project_milestone": "專案里程碑",
            "linus_violation": "違反Linus原則警告",
            "architecture_decision": "架構決策記錄",
            "code_review_result": "程式碼審查結果",
            "system_startup": "系統啟動",
            "error_occurred": "系統錯誤"
        }
        
        # 任務類型定義
        self.task_types = {
            "system_design": "系統架構設計",
            "feature_dev": "新功能開發",
            "bug_fix": "問題修復", 
            "code_review": "程式碼審查",
            "refactor": "程式碼重構",
            "testing": "測試實作",
            "documentation": "文檔撰寫",
            "performance_optimization": "效能優化",
            "general": "一般任務"
        }
        
        # 內存快取和執行緒鎖
        self._events_cache = None
        self._cache_timestamp = None
        self._cache_lock = threading.Lock()
        self._file_lock = threading.Lock()
        
        # 初始化專案檔案
        self._initialize_project_file()
        
        logger.info(f"EventRecorder initialized with data path: {self.data_path}")
    
    def _initialize_project_file(self):
        """初始化專案事件檔案"""
        if not self.events_file.exists():
            initial_data = {
                "project_meta": {
                    "created": datetime.now().isoformat(),
                    "name": "ai-dev-platform",
                    "version": "1.0.0",
                    "tech_stack": {}
                },
                "events": []
            }
            self._write_events_file(initial_data)
            logger.info("Created new project events file")
        
        # 記錄系統啟動事件
        self.append_system_event("system_startup", {
            "timestamp": datetime.now().isoformat(),
            "message": "EventRecorder system started"
        })
    
    def _read_events_file(self) -> Dict[str, Any]:
        """讀取事件檔案"""
        try:
            with self._file_lock:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading events file: {str(e)}")
            return {"project_meta": {}, "events": []}
    
    def _write_events_file(self, data: Dict[str, Any]):
        """寫入事件檔案"""
        try:
            with self._file_lock:
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        'w',
                        encoding='utf-8',
                        delete=False,
                        dir=self.events_file.parent
                    ) as temp_file:
                        temp_path = Path(temp_file.name)
                        json.dump(data, temp_file, ensure_ascii=False, indent=2)
                        temp_file.flush()
                        os.fsync(temp_file.fileno())
                except Exception:
                    if temp_path and temp_path.exists():
                        try:
                            temp_path.unlink()
                        except OSError:
                            pass
                    raise

                if self.events_file.exists():
                    backup_name = f"project_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = self.backup_dir / backup_name
                    try:
                        shutil.copy2(self.events_file, backup_path)
                    except Exception as backup_error:
                        logger.warning(
                            f"Failed to create backup before updating events file: {backup_error}"
                        )

                if temp_path is not None:
                    temp_path.replace(self.events_file)

                # 清除快取
                with self._cache_lock:
                    self._events_cache = None

        except Exception as e:
            logger.error(f"Error writing events file: {str(e)}")
            raise
    
    def _get_cached_data(self) -> Optional[Dict[str, Any]]:
        """獲取快取的資料"""
        with self._cache_lock:
            if (self._events_cache is not None and 
                self._cache_timestamp is not None and
                time.time() - self._cache_timestamp < 30):  # 30秒快取
                return self._events_cache
        return None
    
    def _update_cache(self, data: Dict[str, Any]):
        """更新快取"""
        with self._cache_lock:
            self._events_cache = data
            self._cache_timestamp = time.time()
    
    def append_work_report(self, work_report_data: Dict[str, Any], file_changes: List[str] = None):
        """記錄AI工作報告事件"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": "work_report",
                "ai_config": work_report_data.get('ai_config', {}),
                "summary": self._generate_work_summary(work_report_data),
                "work_report": self._extract_report_content(work_report_data),
                "file_changes": file_changes or [],
                "processing_status": work_report_data.get('processing_status', 'unknown')
            }
            
            self._append_event(event)
            logger.info(f"Recorded work report from {event['ai_config'].get('provider')}/{event['ai_config'].get('role')}")
            
        except Exception as e:
            logger.error(f"Error recording work report: {str(e)}")
    
    def append_ai_handover(self, from_ai: Dict[str, str], to_ai: Dict[str, str], 
                          reason: str, context: Dict[str, Any]):
        """記錄AI切換交接事件"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": "ai_handover",
                "from_ai": from_ai,
                "to_ai": to_ai,
                "reason": reason,
                "context": context,
                "summary": f"AI切換：{from_ai.get('provider', 'Unknown')}/{from_ai.get('role', 'Unknown')} → {to_ai.get('provider', 'Unknown')}/{to_ai.get('role', 'Unknown')}"
            }
            
            self._append_event(event)
            logger.info(f"Recorded AI handover: {event['summary']}")
            
        except Exception as e:
            logger.error(f"Error recording AI handover: {str(e)}")
    
    def append_file_change(self, file_path: str, change_type: str, ai_name: str = None, 
                          change_summary: str = None):
        """記錄檔案變更事件"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": "file_change",
                "file_path": file_path,
                "change_type": change_type,  # created, modified, deleted
                "ai_name": ai_name,
                "change_summary": change_summary,
                "summary": f"檔案{change_type}：{file_path}"
            }
            
            self._append_event(event)
            logger.info(f"Recorded file change: {event['summary']}")
            
        except Exception as e:
            logger.error(f"Error recording file change: {str(e)}")
    
    def append_linus_violation(self, violation_details: Dict[str, Any], ai_config: Dict[str, str]):
        """記錄Linus原則違反警告"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": "linus_violation",
                "ai_config": ai_config,
                "violation_details": violation_details,
                "severity": violation_details.get('severity', 'medium'),
                "summary": f"Linus原則違反：{violation_details.get('principle', 'Unknown')}"
            }
            
            self._append_event(event)
            logger.warning(f"Recorded Linus violation: {event['summary']}")
            
        except Exception as e:
            logger.error(f"Error recording Linus violation: {str(e)}")
    
    def append_system_event(self, event_type: str, event_data: Dict[str, Any]):
        """記錄系統事件"""
        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "type": event_type,
                "data": event_data,
                "summary": event_data.get('message', f'{event_type} event')
            }
            
            self._append_event(event)
            logger.info(f"Recorded system event: {event['summary']}")
            
        except Exception as e:
            logger.error(f"Error recording system event: {str(e)}")
    
    def _append_event(self, event: Dict[str, Any]):
        """內部方法：添加事件到檔案"""
        data = self._read_events_file()
        data['events'].append(event)
        self._write_events_file(data)
        self._update_cache(data)
    
    def _generate_work_summary(self, work_report_data: Dict[str, Any]) -> str:
        """生成工作報告摘要"""
        ai_config = work_report_data.get('ai_config', {})
        user_message = work_report_data.get('user_message', '')
        
        provider = ai_config.get('provider', 'Unknown')
        role = ai_config.get('role', 'Unknown')
        
        # 簡單的任務類型檢測
        task_type = "一般任務"
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ['設計', '架構', 'design', 'architecture']):
            task_type = "架構設計"
        elif any(word in user_lower for word in ['實作', '程式碼', 'code', 'implement']):
            task_type = "功能開發"
        elif any(word in user_lower for word in ['修復', 'bug', 'fix']):
            task_type = "問題修復"
        elif any(word in user_lower for word in ['審查', 'review']):
            task_type = "程式碼審查"
        
        return f"{provider}/{role} - {task_type}"
    
    def _extract_report_content(self, work_report_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取工作報告的核心內容"""
        return {
            "user_message": work_report_data.get('user_message', '')[:200],  # 限制長度
            "ai_response": work_report_data.get('ai_response', '')[:500],    # 限制長度
            "work_report": work_report_data.get('work_report', {}),
            "linus_compliance": work_report_data.get('linus_compliance', {})
        }
    
    def get_recent_events(self, limit: int = 10, event_types: List[str] = None) -> List[Dict[str, Any]]:
        """獲取最近的事件"""
        try:
            # 嘗試從快取獲取
            data = self._get_cached_data()
            if data is None:
                data = self._read_events_file()
                self._update_cache(data)
            
            events = data.get('events', [])
            
            # 過濾事件類型
            if event_types:
                events = [e for e in events if e.get('type') in event_types]
            
            # 按時間戳排序並限制數量
            events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent events: {str(e)}")
            return []
    
    def get_events_by_ai(self, ai_provider: str = None, ai_role: str = None, 
                        limit: int = 20) -> List[Dict[str, Any]]:
        """根據AI配置獲取事件"""
        try:
            data = self._get_cached_data() or self._read_events_file()
            events = data.get('events', [])
            
            filtered_events = []
            for event in events:
                ai_config = event.get('ai_config', {})
                
                if ai_provider and ai_config.get('provider') != ai_provider:
                    continue
                if ai_role and ai_config.get('role') != ai_role:
                    continue
                
                filtered_events.append(event)
            
            # 按時間戳排序並限制數量
            filtered_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return filtered_events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting events by AI: {str(e)}")
            return []
    
    def search_events(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索歷史事件"""
        try:
            data = self._get_cached_data() or self._read_events_file()
            events = data.get('events', [])
            
            results = []
            query_lower = query.lower()
            
            for event in events:
                # 文本搜索
                searchable_text = json.dumps(event, ensure_ascii=False).lower()
                if query_lower in searchable_text:
                    results.append(event)
                    continue
                
                # 特定欄位搜索
                if (query_lower in event.get('summary', '').lower() or
                    query_lower in event.get('type', '').lower()):
                    results.append(event)
            
            # 應用過濾器
            if filters:
                if 'event_type' in filters:
                    results = [e for e in results if e.get('type') == filters['event_type']]
                
                if 'ai_provider' in filters:
                    results = [e for e in results 
                              if e.get('ai_config', {}).get('provider') == filters['ai_provider']]
                
                if 'date_from' in filters:
                    results = [e for e in results if e.get('timestamp', '') >= filters['date_from']]
                
                if 'date_to' in filters:
                    results = [e for e in results if e.get('timestamp', '') <= filters['date_to']]
            
            # 按時間戳排序
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return results[:100]  # 限制結果數量
            
        except Exception as e:
            logger.error(f"Error searching events: {str(e)}")
            return []
    
    def rebuild_project_state(self) -> Dict[str, Any]:
        """從事件流重建專案當前狀態"""
        try:
            data = self._get_cached_data() or self._read_events_file()
            events = data.get('events', [])
            
            state = {
                'project_meta': data.get('project_meta', {}),
                'total_events': len(events),
                'event_statistics': self._calculate_event_statistics(events),
                'recent_activity': self._summarize_recent_activity(events),
                'ai_usage_stats': self._calculate_ai_usage_stats(events),
                'file_change_summary': self._summarize_file_changes(events),
                'linus_compliance_summary': self._summarize_linus_compliance(events),
                'last_updated': datetime.now().isoformat()
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error rebuilding project state: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_event_statistics(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """計算事件統計"""
        stats = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            stats[event_type] = stats.get(event_type, 0) + 1
        return stats
    
    def _summarize_recent_activity(self, events: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
        """總結最近的活動"""
        from datetime import timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        recent_events = [e for e in events if e.get('timestamp', '') >= cutoff_date]
        
        return {
            'total_recent_events': len(recent_events),
            'event_types': self._calculate_event_statistics(recent_events),
            'most_recent': recent_events[-1] if recent_events else None
        }
    
    def _calculate_ai_usage_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """計算AI使用統計"""
        providers = {}
        roles = {}
        
        for event in events:
            ai_config = event.get('ai_config', {})
            provider = ai_config.get('provider')
            role = ai_config.get('role')
            
            if provider:
                providers[provider] = providers.get(provider, 0) + 1
            if role:
                roles[role] = roles.get(role, 0) + 1
        
        return {
            'by_provider': providers,
            'by_role': roles
        }
    
    def _summarize_file_changes(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """總結檔案變更"""
        file_events = [e for e in events if e.get('type') == 'file_change']
        
        changes = {'created': 0, 'modified': 0, 'deleted': 0}
        affected_files = set()
        
        for event in file_events:
            change_type = event.get('change_type', 'unknown')
            if change_type in changes:
                changes[change_type] += 1
            
            file_path = event.get('file_path')
            if file_path:
                affected_files.add(file_path)
        
        return {
            'change_counts': changes,
            'total_affected_files': len(affected_files),
            'recent_changes': file_events[-10:] if file_events else []
        }
    
    def _summarize_linus_compliance(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """總結Linus原則合規性"""
        violations = [e for e in events if e.get('type') == 'linus_violation']
        
        severity_counts = {}
        for violation in violations:
            severity = violation.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_violations': len(violations),
            'by_severity': severity_counts,
            'recent_violations': violations[-5:] if violations else []
        }
    
    def get_project_metadata(self) -> Dict[str, Any]:
        """獲取專案元資料"""
        try:
            data = self._read_events_file()
            return data.get('project_meta', {})
        except Exception as e:
            logger.error(f"Error getting project metadata: {str(e)}")
            return {}
    
    def update_project_metadata(self, metadata_updates: Dict[str, Any]):
        """更新專案元資料"""
        try:
            data = self._read_events_file()
            data['project_meta'].update(metadata_updates)
            data['project_meta']['last_updated'] = datetime.now().isoformat()
            self._write_events_file(data)
            
            logger.info("Updated project metadata")
            
        except Exception as e:
            logger.error(f"Error updating project metadata: {str(e)}")
    
    def export_events(self, output_file: Path, event_types: List[str] = None, 
                     date_range: tuple = None) -> bool:
        """匯出事件到檔案"""
        try:
            data = self._read_events_file()
            events = data.get('events', [])
            
            # 過濾事件
            if event_types:
                events = [e for e in events if e.get('type') in event_types]
            
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                events = [e for e in events 
                         if start_date <= e.get('timestamp', '') <= end_date]
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'project_meta': data.get('project_meta', {}),
                'events_count': len(events),
                'events': events
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(events)} events to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting events: {str(e)}")
            return False


if __name__ == "__main__":
    # 簡單測試
    from pathlib import Path
    
    recorder = EventRecorder(Path("./test_data"))
    
    # 測試記錄工作報告
    test_report = {
        'ai_config': {'provider': 'anthropic', 'model': 'claude-3-5-sonnet-20241022', 'role': 'system_architect'},
        'user_message': '設計一個用戶管理系統',
        'ai_response': '我建議使用JWT認證...',
        'processing_status': 'success'
    }
    
    recorder.append_work_report(test_report)
    
    # 測試獲取最近事件
    recent = recorder.get_recent_events(5)
    print(f"Recent events: {len(recent)}")
    
    # 測試重建專案狀態
    state = recorder.rebuild_project_state()
    print(f"Project state: {json.dumps(state, indent=2, ensure_ascii=False)}")
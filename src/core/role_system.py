"""
角色系統管理 - 三層組合角色配置

基於 Linus 工程哲學設計：
- 統一的角色配置格式（好品味原則）
- 程式類角色強制應用Linus原則
- 簡潔的prompt建構邏輯
"""

import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class RoleSystem:
    """
    角色系統管理器
    
    職責：
    1. 角色配置管理（三層組合：AI供應商/模型/角色）
    2. Prompt建構和合併
    3. 程式類/非程式類角色分工
    4. Linus原則強制適用
    """
    
    def __init__(self, configs_path: Path):
        self.configs_path = Path(configs_path)
        self.configs_path.mkdir(parents=True, exist_ok=True)
        
        # 角色配置
        self.programming_roles = {}
        self.non_programming_roles = {}
        self.ai_providers = {}
        self.linus_prompts = {}
        
        # 載入配置
        self._load_configurations()
        
        logger.info("RoleSystem initialized")
    
    def _load_configurations(self):
        """載入角色配置檔案"""
        try:
            self._load_default_roles()
            self._load_ai_providers()
            self._load_linus_prompts()
            
            # 嘗試載入自訂配置
            roles_file = self.configs_path / "roles.yaml"
            providers_file = self.configs_path / "ai_providers.yaml"
            
            if roles_file.exists():
                self._load_roles_from_file(roles_file)
            
            if providers_file.exists():
                self._load_providers_from_file(providers_file)
                
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            # 使用預設配置繼續運行
    
    def _load_default_roles(self):
        """載入預設角色配置"""
        self.programming_roles = {
            'program_manager': {
                'title': 'Program Manager',
                'focus': ['專案規劃', '需求分析', '進度控制', '資源協調'],
                'linus_aspect': '專案規劃簡潔明確，拒絕過度設計',
                'base_prompt': """你是資深專案經理，專精於：
- 專案整體規劃和需求分析
- 進度控制和資源協調
- 風險評估和問題解決
- 團隊溝通和決策支援"""
            },
            'system_architect': {
                'title': 'System Architect', 
                'focus': ['系統架構', '技術選型', '整體設計', '架構審查'],
                'linus_aspect': '架構設計消除複雜性，追求簡潔elegance',
                'base_prompt': """你是資深系統架構師，專精於：
- 系統架構設計和技術選型
- 程式碼品質審查和重構建議  
- 專案整體規劃和風險評估
- 複雜問題的系統性分析"""
            },
            'coder_programmer': {
                'title': 'Coder Programmer',
                'focus': ['具體功能實作', 'API開發', '程式碼撰寫'],
                'linus_aspect': '程式碼簡潔實用，單一職責，避免過度抽象',
                'base_prompt': """你是資深程式開發者，專精於：
- 具體功能實作和API開發
- 高品質程式碼撰寫
- 演算法優化和性能調校
- 技術問題的實務解決"""
            },
            'coder_reviewer': {
                'title': 'Coder Reviewer',
                'focus': ['程式碼審查', '品質把關', '重構建議', 'best practice'],
                'linus_aspect': '嚴格執行簡潔原則，拒絕複雜設計',
                'base_prompt': """你是程式碼審查專家，專精於：
- 程式碼品質審查和重構建議
- 最佳實踐指導和標準制定
- 架構缺陷識別和改進
- 程式碼安全和效能評估"""
            },
            'devops_engineer': {
                'title': 'DevOps Engineer',
                'focus': ['部署自動化', 'CI/CD', '環境配置', '監控'],
                'linus_aspect': '部署流程簡單可靠，避免過度複雜的工具鏈',
                'base_prompt': """你是DevOps工程師，專精於：
- 部署自動化和CI/CD流程
- 環境配置和基礎設施管理
- 監控和日誌分析
- 系統穩定性和災難恢復"""
            },
            'qa_engineer': {
                'title': 'QA Engineer',
                'focus': ['測試策略', '品質保證', 'bug驗證', '測試自動化'],
                'linus_aspect': '測試方法簡潔有效，重點測試核心功能',
                'base_prompt': """你是QA測試工程師，專精於：
- 測試策略設計和品質保證
- 自動化測試和測試框架
- Bug驗證和缺陷分析
- 產品品質評估和改進建議"""
            },
            'performance_optimizer': {
                'title': 'Performance Optimizer',
                'focus': ['效能分析', '優化建議', '瓶頸識別', '資源使用'],
                'linus_aspect': '優化手段簡單直接，避免過早優化',
                'base_prompt': """你是效能優化專家，專精於：
- 系統效能分析和瓶頸識別
- 程式碼和演算法優化
- 資源使用監控和調校
- 擴展性和負載能力評估"""
            },
            'technical_writer': {
                'title': 'Technical Writer',
                'focus': ['技術文檔', 'API文檔', '使用說明', '架構文件'],
                'linus_aspect': '文檔簡潔明確，重點突出，易於理解',
                'base_prompt': """你是技術文件撰寫專家，專精於：
- 技術文檔和API文檔撰寫
- 使用手冊和操作指南
- 架構文件和系統說明
- 開發者文檔和最佳實踐指南"""
            }
        }
        
        self.non_programming_roles = {
            'general_assistant': {
                'title': 'General Assistant',
                'focus': ['一般問答', '資訊查詢', '常識解答'],
                'base_prompt': """你是通用助手，能夠：
- 回答各類一般性問題
- 提供資訊查詢和整理服務
- 協助日常任務和決策支援
- 進行友善和有用的對話"""
            },
            'research_analyst': {
                'title': 'Research Analyst', 
                'focus': ['資料研究', '事實查核', '趨勢分析'],
                'base_prompt': """你是研究分析師，專精於：
- 深度資料研究和分析
- 事實查核和資訊驗證
- 趨勢分析和預測
- 報告撰寫和洞察提供"""
            },
            'creative_consultant': {
                'title': 'Creative Consultant',
                'focus': ['創意發想', '內容創作', '設計建議'],
                'base_prompt': """你是創意顧問，專精於：
- 創意發想和概念開發
- 內容創作和文案撰寫
- 設計建議和美學指導
- 創新思維和解決方案"""
            }
        }
    
    def _load_ai_providers(self):
        """載入AI提供商配置"""
        self.ai_providers = {
            'openai': {
                'name': 'OpenAI',
                'strengths': ['邏輯推理', '程式碼生成', '問題解決'],
                'api_base': 'https://api.openai.com/v1',
                'base_characteristics': '你具有出色的邏輯推理能力和程式碼生成能力，擅長結構化思考和問題解決。'
            },
            'anthropic': {
                'name': 'Anthropic', 
                'strengths': ['系統分析', '架構設計', '程式碼審查'],
                'api_base': 'https://api.anthropic.com/v1',
                'base_characteristics': '你具有強大的系統分析能力，擅長架構設計和程式碼審查，注重安全和可靠性。'
            },
            'xai': {
                'name': 'xAI',
                'strengths': ['創新思維', '另類解法', '優化建議'],
                'api_base': 'https://api.x.ai/v1',
                'base_characteristics': '你具有創新思維和獨特視角，善於提供另類解法和優化建議。'
            },
            'google': {
                'name': 'Google AI',
                'strengths': ['資料處理', '分析能力', '多模態處理'],
                'api_base': 'https://generativelanguage.googleapis.com/v1',
                'base_characteristics': '你具有強大的資料處理和分析能力，擅長多模態資訊處理。'
            }
        }
    
    def _load_linus_prompts(self):
        """載入Linus原則相關的prompt模板"""
        self.linus_prompts = {
            'core_principles': """
【Linus原則強制執行】

1. 好品味原則：
   - 優先設計讓特殊情況消失的解決方案
   - 統一的資料流和處理邏輯
   - 用策略模式消除if/else分支堆積
   - 選擇讓系統更簡潔的方法

2. Never break userspace：
   - 保持向後相容性
   - 不破壞既有的工作流程
   - API設計考慮未來擴展

3. 實用主義：
   - 解決真實存在的問題
   - 拒絕過度設計和不必要的抽象層
   - 選擇已被驗證的成熟方法
   - 避免為想像中的需求設計

4. 簡潔執念：
   - 系統架構層次清晰，不超過3層縮排
   - 每個模組單一職責
   - 函數長度控制在50行以內
   - 依賴關係明確簡單

記住：如果需要大量解釋的設計，通常不是好設計。
            """,
            
            'decision_framework': """
【技術決策框架】

每個技術選擇都必須通過以下檢驗：

1. 簡潔性檢查：
   - 這個選擇是否讓系統更簡單？
   - 是否引入不必要的抽象層？
   - 能否用更直接的方式解決？

2. 實用性檢查：
   - 這個選擇是否解決真實存在的問題？
   - 是否會為未來可能不存在的需求增加複雜度？
   - 維護成本是否合理？

3. 品味檢查：
   - 這個設計是否讓特殊情況變少？
   - 是否讓相似的東西用相似的方式處理？
   - 新手能否快速理解？
            """,
            
            'code_review_criteria': """
【程式碼審查標準】

按優先級排序：

1. 簡潔性審查（最高優先）：
   - 縮排是否超過3層？
   - 函數是否超過50行？
   - 是否有不必要的抽象層？

2. 好品味檢查：
   - 特殊情況是否可以消除？
   - 相似功能是否用統一方式處理？
   - 是否存在重複的條件判斷邏輯？

3. 實用主義評估：
   - 程式碼是否解決真實問題？
   - 是否為未來可能的需求過度設計？
   - 依賴的外部套件是否必要？

對複雜設計零容忍，直接指出問題並要求重構。
            """
        }
    
    def build_role_prompt(self, ai_provider: str, model: str, role: str, 
                         project_context: Dict[str, Any], custom_prompt: str = None) -> str:
        """建構完整的角色prompt"""
        try:
            # 1. 基礎AI特性
            base_prompt = self.ai_providers.get(ai_provider, {}).get('base_characteristics', '')
            
            # 2. 專業角色基礎
            role_data = self._get_role_data(role)
            role_prompt = role_data.get('base_prompt', f'你是一個{role}角色。')
            
            # 3. 專案特定上下文
            project_prompt = self._build_project_context_prompt(project_context)
            
            # 4. 自訂覆蓋
            custom_section = f"\n\n【特殊要求】\n{custom_prompt}" if custom_prompt else ""
            
            # 5. Linus原則強制適用（程式類角色）
            if self._is_programming_role(role):
                linus_enforcement = self._get_linus_enforcement_prompt(role)
                
                merged_prompt = f"""
{base_prompt}

{role_prompt}

{project_prompt}

{linus_enforcement}

{custom_section}

【重要】身為程式類角色，你必須在所有與程式相關的討論中嚴格遵循Linus簡潔原則。
                """.strip()
            else:
                merged_prompt = f"""
{base_prompt}

{role_prompt}

{project_prompt}

{custom_section}
                """.strip()
            
            return merged_prompt
            
        except Exception as e:
            logger.error(f"Error building role prompt: {str(e)}")
            # 降級到基本prompt
            return f"你是一個{role}，請協助使用者完成任務。"
    
    def _get_role_data(self, role: str) -> Dict[str, Any]:
        """獲取角色資料"""
        if role in self.programming_roles:
            return self.programming_roles[role]
        elif role in self.non_programming_roles:
            return self.non_programming_roles[role]
        else:
            return {'base_prompt': f'你是一個{role}角色。'}
    
    def _is_programming_role(self, role: str) -> bool:
        """檢查是否為程式類角色"""
        return role in self.programming_roles
    
    def _get_linus_enforcement_prompt(self, role: str) -> str:
        """根據角色獲取Linus原則強制prompt"""
        role_data = self.programming_roles.get(role, {})
        linus_aspect = role_data.get('linus_aspect', '遵循Linus簡潔原則')
        
        base_linus = self.linus_prompts['core_principles']
        
        # 針對不同角色的特殊要求
        role_specific = ""
        if role == 'system_architect':
            role_specific = """
在架構決策時，請明確說明：
- 為什麼這個設計符合簡潔原則
- 如何避免不必要的複雜性
- 這個選擇如何讓特殊情況變少

如果遇到複雜需求，優先考慮：
1. 能否重新定義問題讓它變簡單
2. 能否用現有簡單工具解決
3. 複雜方案的維護成本是否合理
            """
        elif role == 'coder_reviewer':
            role_specific = self.linus_prompts['code_review_criteria']
        elif role == 'coder_programmer':
            role_specific = """
程式碼實作要求：
- 縮排不超過3層，超過需要重構
- 函數長度不超過50行
- 變數命名簡潔明確
- 單一職責，避免複雜的條件邏輯
- 錯誤處理要優雅降級

如果程式碼需要大量註解解釋，通常表示設計有問題。
            """
        
        return f"{base_linus}\n\n【角色特殊要求】\n{linus_aspect}\n{role_specific}"
    
    def _build_project_context_prompt(self, project_context: Dict[str, Any]) -> str:
        """建構專案上下文prompt"""
        if not project_context:
            return ""
        
        context_parts = ["【專案上下文】"]
        
        if 'recent_events' in project_context:
            context_parts.append("最近的專案活動：")
            for event in project_context['recent_events'][:3]:  # 只顯示最近3個
                event_summary = event.get('summary', event.get('type', 'Unknown event'))
                context_parts.append(f"- {event_summary}")
        
        if 'current_ai' in project_context and project_context['current_ai']:
            current = project_context['current_ai']
            context_parts.append(f"當前AI配置：{current.get('provider')}/{current.get('model')}/{current.get('role')}")
        
        return "\n".join(context_parts) if len(context_parts) > 1 else ""
    
    def get_role_capabilities(self, role: str) -> Dict[str, Any]:
        """獲取角色能力和專長"""
        role_data = self._get_role_data(role)
        
        return {
            'title': role_data.get('title', role),
            'focus': role_data.get('focus', []),
            'is_programming_role': self._is_programming_role(role),
            'linus_aspect': role_data.get('linus_aspect'),
            'strengths': role_data.get('focus', [])
        }
    
    def validate_role_assignment(self, task_type: str, assigned_role: str) -> Dict[str, Any]:
        """驗證角色分配是否合適"""
        role_capabilities = self.get_role_capabilities(assigned_role)
        
        # 簡單的任務類型與角色匹配邏輯
        task_role_mapping = {
            'system_design': ['system_architect', 'program_manager'],
            'feature_dev': ['coder_programmer', 'system_architect'],
            'bug_fix': ['coder_programmer', 'coder_reviewer'],
            'code_review': ['coder_reviewer', 'system_architect'],
            'refactor': ['coder_reviewer', 'coder_programmer'],
            'testing': ['qa_engineer', 'coder_programmer'],
            'documentation': ['technical_writer', 'system_architect'],
            'performance_optimization': ['performance_optimizer', 'system_architect'],
            'deployment': ['devops_engineer', 'system_architect'],
            'general': ['general_assistant', 'research_analyst']
        }
        
        suitable_roles = task_role_mapping.get(task_type, [assigned_role])
        is_suitable = assigned_role in suitable_roles
        
        return {
            'is_suitable': is_suitable,
            'task_type': task_type,
            'assigned_role': assigned_role,
            'recommended_roles': suitable_roles,
            'role_capabilities': role_capabilities,
            'suggestion': 'Role assignment is appropriate' if is_suitable else f'Consider using one of: {", ".join(suitable_roles)}'
        }
    
    def get_available_roles(self, include_programming: bool = True, 
                           include_non_programming: bool = True) -> Dict[str, Any]:
        """獲取可用角色列表"""
        roles = {}
        
        if include_programming:
            roles.update({k: v for k, v in self.programming_roles.items()})
        
        if include_non_programming:
            roles.update({k: v for k, v in self.non_programming_roles.items()})
        
        return roles
    
    def get_available_ai_providers(self) -> Dict[str, Any]:
        """獲取可用AI提供商列表"""
        return self.ai_providers.copy()
    
    def _load_roles_from_file(self, file_path: Path):
        """從檔案載入角色配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'programming_roles' in data:
                self.programming_roles.update(data['programming_roles'])
            
            if 'non_programming_roles' in data:
                self.non_programming_roles.update(data['non_programming_roles'])
                
            logger.info(f"Loaded roles from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading roles from {file_path}: {str(e)}")
    
    def _load_providers_from_file(self, file_path: Path):
        """從檔案載入AI提供商配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if 'providers' in data:
                self.ai_providers.update(data['providers'])
                
            logger.info(f"Loaded providers from {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading providers from {file_path}: {str(e)}")


if __name__ == "__main__":
    # 簡單測試
    from pathlib import Path
    
    role_system = RoleSystem(Path("./test_configs"))
    
    # 測試角色prompt建構
    prompt = role_system.build_role_prompt(
        'anthropic', 
        'claude-3-5-sonnet-20241022', 
        'system_architect',
        {'session_id': 'test123'}
    )
    
    print("Generated prompt:")
    print(prompt)
    
    # 測試角色驗證
    validation = role_system.validate_role_assignment('system_design', 'coder_programmer')
    print(f"\nRole validation: {json.dumps(validation, indent=2, ensure_ascii=False)}")
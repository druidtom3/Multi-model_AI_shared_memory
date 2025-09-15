# 多AI協作開發平台

基於 **Linus Torvalds 工程哲學** 的多AI協作開發平台，支援 OpenAI、Anthropic、xAI、Google AI 等多家供應商的統一整合。

## 🎯 核心特色

### Linus 工程哲學驅動
- **好品味原則**: 讓特殊情況消失，統一資料結構
- **Never break userspace**: 嚴格向後相容性
- **實用主義**: 解決真實問題，拒絕過度設計
- **簡潔執念**: 系統架構清晰，複雜度最小化

### 多AI協作能力
- 🤖 支援 **OpenAI, Anthropic, xAI, Google AI** 四大AI供應商
- 🎭 **智能角色系統**: 8種程式類角色 + 3種一般助理角色
- 🔄 **無縫角色切換**: 保持完整的對話上下文
- 📝 **強制工作報告**: 每個AI都必須提供結構化報告

### 專案記憶與追蹤
- 📚 **統一事件流**: JSON格式記錄所有專案歷史
- 🔍 **智能檢索**: 支援事件搜尋和狀態重建
- 📊 **專案儀表板**: 即時監控開發進度
- 🛡️ **Linus原則合規檢查**: 自動檢查程式類工作是否符合簡潔原則

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 克隆或下載專案
cd ai-dev-platform

# 安裝Python依賴
pip install -r requirements.txt
```

### 2. 配置API金鑰

複製環境變數範本：
```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入你的API金鑰：
```env
# 至少需要配置一個AI供應商的API金鑰
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
XAI_API_KEY=your_xai_api_key_here
GOOGLE_AI_KEY=your_google_ai_api_key_here
```

### 3. 啟動平台

#### Windows:
```cmd
python src\web\app.py
```

#### Linux/Mac:
```bash
python src/web/app.py
```

### 4. 訪問Web界面

開啟瀏覽器訪問: `http://127.0.0.1:5000`

## 📁 專案結構

```
ai-dev-platform/
├── src/                           # 核心程式碼
│   ├── core/                      # 核心模組
│   │   ├── ai_coordinator.py      # 主要協調器
│   │   ├── role_system.py         # 角色系統管理
│   │   └── event_recorder.py      # 事件流記錄
│   ├── ai_services/               # AI服務模組
│   │   └── api_clients.py         # AI API客戶端
│   └── web/                       # Web界面
│       ├── app.py                 # Flask應用主檔
│       └── templates/             # HTML範本
├── workspace/                     # 程式碼工作空間
├── data/                          # 資料存儲
│   └── project_events.json        # 事件流記錄
├── configs/                       # 配置檔案
│   ├── ai_providers.yaml          # AI供應商配置
│   └── roles.yaml                 # 角色定義
├── requirements.txt               # Python依賴
├── .env.example                   # 環境變數範本
└── README.md                      # 專案說明
```

## 🎭 AI角色系統

### 程式類角色 (強制遵循Linus原則)

| 角色 | 專長 | Linus原則重點 |
|------|------|---------------|
| **Program Manager** | 專案規劃、需求分析 | 專案規劃簡潔明確，拒絕過度設計 |
| **System Architect** | 系統架構、技術選型 | 架構設計消除複雜性，追求簡潔elegance |
| **Coder Programmer** | 功能實作、程式碼撰寫 | 程式碼簡潔實用，單一職責 |
| **Coder Reviewer** | 程式碼審查、品質把關 | 嚴格執行簡潔原則，拒絕複雜設計 |
| **DevOps Engineer** | 部署自動化、CI/CD | 部署流程簡單可靠 |
| **QA Engineer** | 測試策略、品質保證 | 測試方法簡潔有效 |
| **Performance Optimizer** | 效能分析、優化建議 | 優化手段簡單直接，避免過早優化 |
| **Technical Writer** | 技術文檔、API文檔 | 文檔簡潔明確，重點突出 |

### 一般助理角色

- **General Assistant**: 一般問答、資訊查詢
- **Research Analyst**: 資料研究、事實查核
- **Creative Consultant**: 創意發想、內容創作

## 🔧 使用方式

### 基本對話流程

1. **選擇AI配置**: 在Web界面選擇 AI供應商 + 模型 + 角色
2. **開始對話**: 描述您的開發需求或問題
3. **查看報告**: AI完成後自動顯示詳細工作報告
4. **切換角色**: 根據需要切換到其他AI配置繼續工作

### AI交接範例

```
使用者: 選擇 Claude + Sonnet + System Architect，請設計用戶管理系統

Claude (System Architect): 
從系統架構師角度，我設計了基於JWT + RBAC的簡潔架構...
[詳細架構設計 + Linus原則合規性分析]

使用者: 切換到 GPT + 4o + Coder Programmer 實作前端

GPT (Coder Programmer): 
收到架構師的設計。基於簡潔原則，我來實作前端組件...
[具體程式碼實作]
```

### 事件流記錄

系統會自動記錄：
- ✅ AI工作報告
- ✅ 角色切換事件
- ✅ 檔案變更記錄
- ✅ Linus原則違反警告
- ✅ 專案里程碑

## ⚙️ 配置選項

### 環境變數說明

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| `DEFAULT_AI_PROVIDER` | 預設AI供應商 | `anthropic` |
| `DEFAULT_MODEL` | 預設模型 | `claude-3-5-sonnet-20241022` |
| `DEFAULT_ROLE` | 預設角色 | `system_architect` |
| `ENFORCE_LINUS_PRINCIPLES` | 是否強制執行Linus原則 | `true` |
| `WEB_HOST` | Web服務器主機 | `127.0.0.1` |
| `WEB_PORT` | Web服務器埠 | `5000` |

### 自訂角色配置

編輯 `configs/roles.yaml` 可以：
- 修改現有角色的專長和prompt
- 添加自訂角色
- 調整角色推薦規則

## 🔍 API文檔

### 主要API端點

- `POST /api/chat` - AI對話
- `POST /api/switch-ai` - 切換AI配置
- `GET /api/project-status` - 獲取專案狀態
- `GET /api/events` - 獲取事件列表
- `POST /api/test-connection` - 測試AI連接

### API調用範例

```javascript
// AI對話
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "設計一個簡潔的用戶認證系統",
        ai_config: {
            provider: "anthropic",
            model: "claude-3-5-sonnet-20241022", 
            role: "system_architect"
        }
    })
});
```

## 🛡️ Linus原則檢查

### 自動檢查項目

程式類角色的工作會自動檢查：

1. **好品味檢查**
   - 是否讓特殊情況消失？
   - 相似功能是否統一處理？

2. **簡潔性檢查**
   - 複雜度是否最小化？
   - 是否有不必要的抽象層？

3. **實用主義檢查**
   - 是否解決真實問題？
   - 是否避免過度設計？

4. **向後相容檢查**
   - API是否保持相容？
   - 工作流程是否被破壞？

### 違反處理

- 🚨 **警告記錄**: 自動記錄到事件流
- 📊 **統計追蹤**: 違反次數和類型統計
- 🔧 **改進建議**: 提供具體的修正建議

## 🚀 進階功能

### 專案狀態重建

系統可以從事件流完全重建專案狀態：

```bash
python -c "
from src.core.event_recorder import EventRecorder
recorder = EventRecorder('./data')
state = recorder.rebuild_project_state()
print(state)
"
```

### 事件搜尋和分析

```bash
# 搜尋特定類型的事件
python -c "
from src.core.event_recorder import EventRecorder
recorder = EventRecorder('./data')
events = recorder.search_events('架構設計')
print(len(events), 'events found')
"
```

### 批次處理和自動化

系統支援程式化調用：

```python
from src.core.ai_coordinator import SyncAICoordinator

coordinator = SyncAICoordinator('./workspace')

# 自動化工作流程
result = coordinator.chat_with_ai({
    'provider': 'anthropic',
    'model': 'claude-3-5-sonnet-20241022',
    'role': 'system_architect'
}, "設計用戶管理系統")

print(result['ai_response'])
```

## 🔧 故障排除

### 常見問題

**Q: API調用失敗**
```
錯誤: API key not found
解決: 檢查 .env 檔案中的API金鑰配置
```

**Q: 模組導入錯誤**
```
錯誤: ModuleNotFoundError
解決: 確認在正確目錄執行，檢查 Python 路徑
```

**Q: 檔案權限錯誤**
```
錯誤: PermissionError
解決: 確認 data/ 和 workspace/ 目錄有寫入權限
```

### 日誌檢查

系統日誌位於 `data/ai_coordinator.log`：

```bash
tail -f data/ai_coordinator.log
```

### 偵錯模式

設置環境變數啟用偵錯：

```bash
export WEB_DEBUG=true
python src/web/app.py
```

## 🤝 貢獻指南

歡迎貢獻！請遵循Linus工程哲學：

1. **簡潔性優先**: 新功能必須讓系統更簡單
2. **實用主義**: 解決真實存在的問題
3. **向後相容**: 不破壞既有功能
4. **好品味**: 消除特殊情況，統一處理方式

### 開發環境設置

```bash
# 安裝開發依賴
pip install -r requirements.txt

# 執行測試
python -m pytest tests/

# 程式碼格式化
black src/

# 型別檢查
mypy src/
```

## 📝 版本歷史

- **v1.0.0** (2024-09-15)
  - 初始版本發布
  - 支援四大AI供應商
  - 完整的角色系統和Linus原則檢查
  - Web界面和API支援

## 📄 授權

本專案採用 MIT 授權條款。

## 🙏 致謝

- **Linus Torvalds** - 提供簡潔工程哲學的啟發
- **OpenAI, Anthropic, xAI, Google AI** - 提供強大的AI服務
- **Flask** - 簡潔的Web框架選擇

---

**記住**: 好的設計應該明顯到不需要解釋為什麼它是對的。 - Linus Torvalds
# 快速開始指南

## 🚀 立即啟動

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 配置API金鑰
```bash
# 複製配置範本
copy .env.example .env

# 編輯 .env 檔案，至少設置一個AI供應商的API金鑰
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# XAI_API_KEY=your_key_here  
# GOOGLE_AI_KEY=your_key_here
```

### 3. 測試系統
```bash
python simple_test.py
```

### 4. 啟動平台
```bash
python start.py
```

### 5. 訪問Web界面
開啟瀏覽器訪問: http://127.0.0.1:5000

## 🎯 核心功能

### AI角色系統
- **8種程式類角色** (遵循Linus原則)
  - System Architect (系統架構師)
  - Coder Programmer (程式開發者)  
  - Coder Reviewer (程式碼審查員)
  - DevOps Engineer (維運工程師)
  - QA Engineer (測試工程師)
  - Performance Optimizer (效能優化師)
  - Technical Writer (技術文件撰寫師)
  - Program Manager (專案經理)

- **3種一般助理角色**
  - General Assistant (通用助手)
  - Research Analyst (研究分析師)
  - Creative Consultant (創意顧問)

### 支援的AI供應商
- **OpenAI**: GPT-4o, GPT-4o Mini, o1-preview, o1-mini
- **Anthropic**: Claude Sonnet, Claude Opus, Claude Haiku  
- **xAI**: Grok Beta
- **Google AI**: Gemini 1.5 Pro, Gemini 1.5 Flash

## 🔧 使用方式

### 基本工作流程
1. **選擇AI配置**: AI供應商 + 模型 + 專業角色
2. **開始對話**: 描述開發需求或問題
3. **查看工作報告**: AI完成後自動生成結構化報告
4. **切換角色**: 根據需要切換到其他AI配置繼續工作

### 範例對話流程
```
使用者選擇: Claude + Sonnet + System Architect
輸入: "設計一個簡潔的用戶認證系統"

Claude回應: [提供架構設計 + Linus原則分析]

使用者切換到: GPT + 4o + Coder Programmer  
輸入: "基於架構師的設計，實作登入API"

GPT回應: [具體程式碼實作]
```

## 📁 專案結構
```
ai-dev-platform/
├── src/core/              # 核心模組
├── src/ai_services/       # AI服務
├── src/web/              # Web界面  
├── configs/              # 配置檔案
├── data/                 # 資料存儲
├── workspace/            # 工作空間
├── start.py             # 啟動腳本
├── simple_test.py       # 系統測試
└── README.md            # 詳細說明
```

## ⚡ 常見問題

**Q: 如何添加新的AI供應商？**
A: 編輯 `configs/ai_providers.yaml` 添加配置，並在 `api_clients.py` 中實作對應的API調用方法。

**Q: 如何自訂角色？**
A: 編輯 `configs/roles.yaml`，可以修改現有角色或添加新角色。

**Q: Linus原則檢查是什麼？**
A: 程式類角色會自動檢查工作是否符合Linus簡潔原則：好品味、簡潔性、實用主義、向後相容。

**Q: 事件流記錄存儲在哪裡？**  
A: 所有專案歷史記錄存儲在 `data/project_events.json`，可以完整重建專案狀態。

## 🛠️ 進階配置

### 自訂Web端口
```env
WEB_HOST=0.0.0.0
WEB_PORT=8080
```

### 啟用調試模式
```env
WEB_DEBUG=true
```

### 強制Linus原則
```env
ENFORCE_LINUS_PRINCIPLES=true
AUTO_COMPLIANCE_CHECK=true
```

## 📞 支援

如遇問題請：
1. 檢查 `data/ai_coordinator.log` 日誌檔案
2. 執行 `python simple_test.py` 診斷系統
3. 確認API金鑰配置正確
4. 檢查網路連接和防火牆設定

---

**記住**: 保持設計簡潔，這是Linus工程哲學的核心精神！
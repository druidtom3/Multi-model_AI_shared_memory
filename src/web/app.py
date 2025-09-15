"""
Flask Web應用 - 多AI協作開發平台Web界面

基於 Linus 工程哲學設計：
- 簡潔的Web界面，重點功能突出
- 統一的路由處理邏輯
- 實用的功能，避免過度複雜的UI
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.exceptions import BadRequest, InternalServerError

# 導入核心模組
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.ai_coordinator import AICoordinator
from core.role_system import RoleSystem
from core.event_recorder import EventRecorder
from ai_services.api_clients import AIAPIClients

logger = logging.getLogger(__name__)

# Flask應用初始化
app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET_KEY', 'dev-secret-key-change-in-production')

# 全局變量
ai_coordinator = None
project_path = None

def init_app():
    """初始化應用和核心組件"""
    global ai_coordinator, project_path
    
    # 設置專案路徑
    project_path = Path(__file__).parent.parent.parent
    
    # 初始化AI協調器
    ai_coordinator = AICoordinator(project_path)
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Flask app initialized")

@app.before_first_request
def setup():
    """應用首次請求前的設置"""
    init_app()

@app.route('/')
def index():
    """主頁 - 顯示平台概覽和當前狀態"""
    try:
        # 獲取專案狀態
        status = ai_coordinator.get_project_status()
        
        # 獲取最近的事件
        recent_events = []
        if ai_coordinator.event_recorder:
            recent_events = ai_coordinator.event_recorder.get_recent_events(limit=5)
        
        # 檢查API金鑰狀態
        api_status = {}
        if ai_coordinator.api_clients:
            api_status = ai_coordinator.api_clients.check_api_keys()
        
        return render_template('index.html', 
                             status=status,
                             recent_events=recent_events,
                             api_status=api_status)
        
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/chat')
def chat():
    """聊天界面 - 與AI進行對話"""
    try:
        # 獲取可用的角色和AI提供商
        available_roles = {}
        available_providers = {}
        
        if ai_coordinator.role_system:
            programming_roles = ai_coordinator.role_system.get_available_roles(True, False)
            non_programming_roles = ai_coordinator.role_system.get_available_roles(False, True)
            available_roles = {
                'programming': programming_roles,
                'non_programming': non_programming_roles
            }
            
            available_providers = ai_coordinator.role_system.get_available_ai_providers()
        
        # 當前AI配置
        current_config = ai_coordinator.current_ai_config or {
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'role': 'system_architect'
        }
        
        return render_template('chat.html',
                             available_roles=available_roles,
                             available_providers=available_providers,
                             current_config=current_config)
        
    except Exception as e:
        logger.error(f"Error loading chat page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API端點 - 處理AI聊天請求"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Missing message'}), 400
        
        message = data['message']
        ai_config = data.get('ai_config', ai_coordinator.current_ai_config)
        custom_role = data.get('custom_role')
        
        if not ai_config:
            return jsonify({'error': 'No AI configuration specified'}), 400
        
        # 使用異步調用AI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_coordinator.chat_with_ai(ai_config, message, custom_role)
            )
            
            return jsonify({
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/switch-ai', methods=['POST'])
def api_switch_ai():
    """API端點 - 切換AI配置"""
    try:
        data = request.get_json()
        
        if not data or 'ai_config' not in data:
            return jsonify({'error': 'Missing AI configuration'}), 400
        
        new_config = data['ai_config']
        handover_context = data.get('handover_context')
        
        result = ai_coordinator.switch_ai_role(new_config, handover_context)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error switching AI: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/project-status')
def api_project_status():
    """API端點 - 獲取專案狀態"""
    try:
        status = ai_coordinator.get_project_status()
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/events')
def api_events():
    """API端點 - 獲取事件列表"""
    try:
        limit = request.args.get('limit', 20, type=int)
        event_types = request.args.getlist('types')
        
        events = []
        if ai_coordinator.event_recorder:
            events = ai_coordinator.event_recorder.get_recent_events(
                limit=limit, 
                event_types=event_types if event_types else None
            )
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """API端點 - 測試AI API連接"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        
        if not provider:
            return jsonify({'error': 'Missing provider'}), 400
        
        if not ai_coordinator.api_clients:
            return jsonify({'error': 'API clients not initialized'}), 500
        
        # 使用異步測試連接
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_coordinator.api_clients.test_connection(provider)
            )
            
            return jsonify({
                'success': True,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/events')
def events_page():
    """事件歷史頁面"""
    try:
        # 獲取事件統計
        events_stats = {}
        recent_events = []
        
        if ai_coordinator.event_recorder:
            state = ai_coordinator.event_recorder.rebuild_project_state()
            events_stats = state.get('event_statistics', {})
            recent_events = ai_coordinator.event_recorder.get_recent_events(limit=50)
        
        return render_template('events.html',
                             events_stats=events_stats,
                             recent_events=recent_events)
        
    except Exception as e:
        logger.error(f"Error loading events page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/settings')
def settings_page():
    """設定頁面"""
    try:
        # 獲取當前設定
        current_settings = {
            'default_provider': os.getenv('DEFAULT_AI_PROVIDER', 'anthropic'),
            'default_model': os.getenv('DEFAULT_MODEL', 'claude-3-5-sonnet-20241022'),
            'default_role': os.getenv('DEFAULT_ROLE', 'system_architect'),
            'enforce_linus': os.getenv('ENFORCE_LINUS_PRINCIPLES', 'true').lower() == 'true',
            'auto_compliance': os.getenv('AUTO_COMPLIANCE_CHECK', 'true').lower() == 'true'
        }
        
        # API金鑰狀態
        api_key_status = {}
        if ai_coordinator.api_clients:
            api_key_status = ai_coordinator.api_clients.check_api_keys()
        
        return render_template('settings.html',
                             current_settings=current_settings,
                             api_key_status=api_key_status)
        
    except Exception as e:
        logger.error(f"Error loading settings page: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.errorhandler(404)
def page_not_found(e):
    """404錯誤處理"""
    return render_template('error.html', 
                         error="頁面不存在", 
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(e):
    """500錯誤處理"""
    logger.error(f"Internal server error: {str(e)}")
    return render_template('error.html', 
                         error="內部伺服器錯誤", 
                         error_code=500), 500

@app.errorhandler(BadRequest)
def bad_request(e):
    """400錯誤處理"""
    return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

def run_app():
    """運行Flask應用"""
    # 從環境變數獲取配置
    host = os.getenv('WEB_HOST', '127.0.0.1')
    port = int(os.getenv('WEB_PORT', 5000))
    debug = os.getenv('WEB_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # 初始化應用（如果直接執行）
    init_app()
    run_app()
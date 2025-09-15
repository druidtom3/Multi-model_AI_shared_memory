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
from typing import Optional, Dict, Any

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.exceptions import HTTPException

# 導入核心模組
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.ai_coordinator import AICoordinator
from core.role_system import RoleSystem
from core.event_recorder import EventRecorder
from utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# Flask應用初始化
app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET_KEY', 'dev-secret-key-change-in-production')

# 全局變量
ai_coordinator = None
project_path = None
error_handler: Optional[ErrorHandler] = None

def init_app():
    """初始化應用和核心組件"""
    global ai_coordinator, project_path, error_handler
    
    # 設置專案路徑
    project_path = Path(__file__).parent.parent.parent
    
    # 初始化AI協調器
    ai_coordinator = AICoordinator(project_path)
    error_handler = ai_coordinator.error_handler
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO)

    logger.info("Flask app initialized")


def _log_and_format_error(error: Exception,
                          context: Optional[Dict[str, Any]] = None,
                          severity: str = "error") -> Dict[str, Any]:
    """Helper to log errors via the shared :class:`ErrorHandler`."""
    if error_handler:
        return error_handler.log_error_with_context(error, context, severity=severity)

    return {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {}
    }

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
        context = {'endpoint': 'index'}
        error_payload = _log_and_format_error(e, context)
        return render_template('error.html',
                               error=error_payload['error'],
                               error_code=500), 500

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
        context = {'endpoint': 'chat'}
        error_payload = _log_and_format_error(e, context)
        return render_template('error.html',
                               error=error_payload['error'],
                               error_code=500), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API端點 - 處理AI聊天請求"""
    data = None
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            context = {'endpoint': 'api_chat', 'reason': 'missing_message'}
            error_payload = _log_and_format_error(
                ValueError('Missing message'),
                context,
                severity='warning'
            )
            return jsonify(error_payload), 400
        
        message = data['message']
        ai_config = data.get('ai_config', ai_coordinator.current_ai_config)
        custom_role = data.get('custom_role')
        
        if not ai_config:
            context = {'endpoint': 'api_chat', 'reason': 'missing_ai_config'}
            error_payload = _log_and_format_error(
                ValueError('No AI configuration specified'),
                context,
                severity='warning'
            )
            return jsonify(error_payload), 400
        
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
        context = {
            'endpoint': 'api_chat',
            'payload_keys': list(data.keys()) if isinstance(data, dict) else None
        }
        error_payload = _log_and_format_error(e, context)
        return jsonify(error_payload), 500

@app.route('/api/switch-ai', methods=['POST'])
def api_switch_ai():
    """API端點 - 切換AI配置"""
    data = None
    try:
        data = request.get_json()
        
        if not data or 'ai_config' not in data:
            context = {'endpoint': 'api_switch_ai', 'reason': 'missing_ai_config'}
            error_payload = _log_and_format_error(
                ValueError('Missing AI configuration'),
                context,
                severity='warning'
            )
            return jsonify(error_payload), 400
        
        new_config = data['ai_config']
        handover_context = data.get('handover_context')
        
        result = ai_coordinator.switch_ai_role(new_config, handover_context)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        context = {
            'endpoint': 'api_switch_ai',
            'payload_keys': list(data.keys()) if isinstance(data, dict) else None
        }
        error_payload = _log_and_format_error(e, context)
        return jsonify(error_payload), 500

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
        context = {'endpoint': 'api_project_status'}
        error_payload = _log_and_format_error(e, context)
        return jsonify(error_payload), 500

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
        context = {
            'endpoint': 'api_events',
            'limit': request.args.get('limit'),
            'types': request.args.getlist('types')
        }
        error_payload = _log_and_format_error(e, context)
        return jsonify(error_payload), 500

@app.route('/api/test-connection', methods=['POST'])
def api_test_connection():
    """API端點 - 測試AI API連接"""
    data = None
    try:
        data = request.get_json()
        provider = data.get('provider') if isinstance(data, dict) else None
        
        if not provider:
            context = {'endpoint': 'api_test_connection', 'reason': 'missing_provider'}
            error_payload = _log_and_format_error(
                ValueError('Missing provider'),
                context,
                severity='warning'
            )
            return jsonify(error_payload), 400

        if not ai_coordinator.api_clients:
            context = {'endpoint': 'api_test_connection', 'reason': 'api_clients_not_initialized'}
            error_payload = _log_and_format_error(
                RuntimeError('API clients not initialized'),
                context
            )
            return jsonify(error_payload), 500
        
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
        context = {
            'endpoint': 'api_test_connection',
            'payload_keys': list(data.keys()) if isinstance(data, dict) else None,
            'provider': data.get('provider') if isinstance(data, dict) else None
        }
        error_payload = _log_and_format_error(e, context)
        return jsonify(error_payload), 500

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
        context = {'endpoint': 'events_page'}
        error_payload = _log_and_format_error(e, context)
        return render_template('error.html',
                               error=error_payload['error'],
                               error_code=500), 500

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
        context = {'endpoint': 'settings_page'}
        error_payload = _log_and_format_error(e, context)
        return render_template('error.html',
                               error=error_payload['error'],
                               error_code=500), 500

@app.errorhandler(Exception)
def handle_unexpected_exception(error: Exception):
    """統一處理未捕捉的例外。"""
    status_code = 500
    severity = 'error'

    if isinstance(error, HTTPException):
        status_code = error.code or status_code
        severity = 'warning' if status_code < 500 else 'error'

    context = {
        'endpoint': 'global_exception_handler',
        'path': request.path,
        'method': request.method,
        'status_code': status_code
    }

    payload = _log_and_format_error(error, context, severity=severity)

    if request.path.startswith('/api/'):
        return jsonify(payload), status_code

    return render_template('error.html',
                           error=payload['error'],
                           error_code=status_code), status_code


@app.errorhandler(404)
def page_not_found(e):
    """404錯誤處理"""
    return render_template('error.html',
                         error="頁面不存在",
                         error_code=404), 404

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
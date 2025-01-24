"""Proxy Error Log API Endpoints"""

from flask import Blueprint, jsonify
from models import db, Proxy, ProxyErrorLog

proxy_error_log_bp = Blueprint('proxy_error_log', __name__)

@proxy_error_log_bp.route('/<proxy_id>/error_logs', methods=['GET'])
def get_proxy_error_logs(proxy_id):
    """Get error logs for a specific proxy"""
    proxy = db.session.get(Proxy, proxy_id)
    if not proxy:
        return jsonify({'message': 'Proxy not found'}), 404

    # Fetch error logs, you can implement pagination if needed
    error_logs = proxy.error_logs.limit(100).all()  # Limit to latest 100 logs
    error_logs_data = [log.to_dict() for log in error_logs]

    return jsonify(error_logs_data), 200

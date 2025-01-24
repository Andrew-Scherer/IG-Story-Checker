"""
Proxy API Routes
Handles proxy management endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from models import db, Proxy, Session, ProxyErrorLog
from sqlalchemy import exc

# Create blueprint
proxy_bp = Blueprint('proxy', __name__)

@proxy_bp.route('/<proxy_id>/error_logs', methods=['GET'])
def get_proxy_error_logs(proxy_id):
    """Get error logs for a specific proxy"""
    try:
        proxy = db.session.get(Proxy, proxy_id)
        if not proxy:
            return create_error_response(
                'not_found',
                f'Proxy {proxy_id} not found',
                {'proxy_id': proxy_id},
                404
            )

        # Fetch error logs, you can implement pagination if needed
        error_logs = proxy.error_logs.limit(100).all()  # Limit to latest 100 logs
        error_logs_data = [log.to_dict() for log in error_logs]

        return jsonify(error_logs_data), 200

    except Exception as e:
        current_app.logger.exception(f"Error fetching error logs for proxy {proxy_id}: {e}")
        return create_error_response(
            'internal_server_error',
            'An unexpected error occurred while fetching error logs.',
            {'error': str(e)},
            500
        )

def log_step(step: str, data: dict = None) -> None:
    """Log a step in the proxy management process"""
    message = f"[PROXY API] {step}"
    if data:
        message += f": {data}"
    current_app.logger.info(message)

def create_error_response(error_type: str, message: str, details: dict = None, status_code: int = 400) -> tuple:
    """Create standardized error response"""
    response = {
        'error': error_type,
        'message': message
    }
    if details:
        response['details'] = details
    current_app.logger.error(f"[PROXY API] Error: {error_type} - {message} - {details}")
    return jsonify(response), status_code

@proxy_bp.route('', methods=['GET'])
def list_proxies():
    """Get all proxies"""
    log_step("Listing all proxies")
    try:
        proxies = Proxy.query.all()
        log_step(f"Found {len(proxies)} proxies")
        return jsonify([{
            **p.to_dict(),
            'sessions': [{
                'id': s.id,
                'session': s.session,
                'status': s.status
            } for s in p.sessions]
        } for p in proxies])
    except Exception as e:
        return create_error_response(
            'database_error',
            'Failed to retrieve proxies',
            {'error': str(e)},
            500
        )

@proxy_bp.route('', methods=['POST'])
def create_proxy():
    """Create new proxy with session in a single transaction"""
    log_step("Starting proxy creation")
    
    try:
        data = request.get_json()
        log_step("Received request data", data)
    except Exception as e:
        return create_error_response(
            'invalid_request',
            'Invalid JSON data',
            {'error': str(e)}
        )

    # Validate required fields
    required_fields = ['ip', 'port', 'session']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return create_error_response(
            'validation_error',
            'Missing required fields',
            {'missing_fields': missing_fields}
        )

    try:
        # Validate port value
        try:
            port = int(data['port'])
        except (ValueError, TypeError):
            return create_error_response(
                'invalid_request',
                'Port must be a valid integer',
                {'port': data['port']}
            )

        log_step("Starting transaction")
        # Create proxy
        # Sanitize IP to remove protocol prefixes
        ip = data['ip']
        if ip.startswith('socks5://'):
            ip = ip[len('socks5://'):]
        log_step("Creating proxy object")
        proxy = Proxy(
            ip=ip,
            port=port,
            username=data.get('username'),
            password=data.get('password'),
            is_active=True
        )
        db.session.add(proxy)
        log_step("Proxy object added to session")
        
        # Create session
        log_step("Creating session object")
        session = Session(
            proxy=proxy,
            session=data['session'],
            status=Session.STATUS_ACTIVE
        )
        db.session.add(session)
        log_step("Session object added to session")
        
        # Commit
        log_step("Committing transaction")
        db.session.commit()
        log_step("Transaction committed successfully")
        
        # Return proxy with session included
        result = {
            **proxy.to_dict(),
            'sessions': [{
                'id': session.id,
                'session': session.session,
                'status': session.status
            }]
        }
        log_step("Returning successful response")
        return jsonify(result), 201

    except exc.IntegrityError as e:
        db.session.rollback()
        log_step("Integrity error occurred", {'error': str(e)})
        error_str = str(e.orig)
        
        if 'sessions_session_key' in error_str:
            return create_error_response(
                'duplicate_session',
                'This session is already in use',
                {'session': data['session']},
                409
            )
        elif 'uix_proxy_ip_port' in error_str:
            return create_error_response(
                'duplicate_proxy',
                'A proxy with this IP and port already exists',
                {'ip': data['ip'], 'port': data['port']},
                409
            )
        return create_error_response(
            'integrity_error',
            'Database constraint violation',
            {'error': error_str},
            400
        )
    except Exception as e:
        db.session.rollback()
        log_step("Unexpected error occurred", {'error': str(e)})
        return create_error_response(
            'creation_failed',
            'Failed to create proxy-session pair',
            {'error': str(e)},
            500
        )

@proxy_bp.route('/<proxy_id>', methods=['DELETE'])
def delete_proxy(proxy_id):
    """Delete proxy"""
    log_step(f"Deleting proxy {proxy_id}")
    proxy = db.session.get(Proxy, proxy_id)
    if not proxy:
        return create_error_response(
            'not_found',
            f'Proxy {proxy_id} not found',
            {'proxy_id': proxy_id},
            404
        )
    
    try:
        # Delete associated sessions first
        log_step(f"Deleting sessions for proxy {proxy_id}")
        Session.query.filter_by(proxy_id=proxy_id).delete()
        db.session.delete(proxy)
        db.session.commit()
        log_step(f"Successfully deleted proxy {proxy_id}")
        return '', 204
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'deletion_failed',
            'Failed to delete proxy',
            {'proxy_id': proxy_id, 'error': str(e)},
            500
        )

@proxy_bp.route('/<proxy_id>/status', methods=['PATCH'])
def update_status(proxy_id):
    """Update proxy status"""
    log_step(f"Updating status for proxy {proxy_id}")
    proxy = db.session.get(Proxy, proxy_id)
    if not proxy:
        return create_error_response(
            'not_found',
            f'Proxy {proxy_id} not found',
            {'proxy_id': proxy_id},
            404
        )
    
    try:
        data = request.get_json()
        log_step("Received status update data", data)
    except Exception as e:
        return create_error_response(
            'invalid_request',
            'Invalid JSON data',
            {'error': str(e)}
        )

    if 'status' not in data:
        return create_error_response(
            'missing_field',
            'Status field is required',
            {'required_field': 'status'}
        )
    
    try:
        new_status = data['status']
        proxy.is_active = (new_status == 'active')
        proxy.status = new_status
        db.session.commit()
        log_step(f"Successfully updated proxy {proxy_id} status to {new_status}")
        return jsonify(proxy.to_dict())
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'update_failed',
            'Failed to update proxy status',
            {'proxy_id': proxy_id, 'error': str(e)},
            500
        )

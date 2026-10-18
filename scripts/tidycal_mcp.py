#!/usr/bin/env python3
"""Read-only TidyCal MCP connector using the documented OAuth 2.1 flow."""
import base64
import hashlib
import http.server
import json
import os
import secrets
import stat
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone

MCP_URL = 'https://tidycal.com/mcp'
RESOURCE_METADATA_URL = 'https://tidycal.com/.well-known/oauth-protected-resource'
AUTH_METADATA_URL = 'https://tidycal.com/.well-known/oauth-authorization-server'
REGISTRATION_URL = 'https://tidycal.com/oauth/register'
REDIRECT_URI = 'http://127.0.0.1:8765/callback'
SCOPE = 'mcp:scheduling:read'
# TidyCal's edge rejects urllib's default "Python-urllib" User-Agent with 403.
USER_AGENT = 'AI-OS-Dashboard/1.0'
CONFIG_PATH = os.path.expanduser(os.environ.get(
    'TIDYCAL_OAUTH_FILE', '~/.config/aios/tidycal-oauth.json'))
_CACHE = {'expires': 0, 'data': None}


class TidyCalError(Exception):
    pass


def _request_json(url, data=None, headers=None, method=None):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or not (parsed.hostname == 'tidycal.com' or
                                         (parsed.hostname or '').endswith('.tidycal.com')):
        raise TidyCalError('Refusing a non-TidyCal or non-HTTPS endpoint.')
    body = None
    request_headers = {'Accept': 'application/json', 'User-Agent': USER_AGENT}
    if headers:
        request_headers.update(headers)
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode()
            request_headers.setdefault('Content-Type', 'application/json')
        else:
            body = urllib.parse.urlencode(data).encode()
            request_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(2_000_001)
    except Exception as exc:
        raise TidyCalError(f'TidyCal request failed: {exc}') from exc
    if len(raw) > 2_000_000:
        raise TidyCalError('TidyCal response exceeded the 2 MB limit.')
    try:
        return json.loads(raw.decode()), response.headers
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TidyCalError('TidyCal returned an invalid JSON response.') from exc


def _save_config(config):
    directory = os.path.dirname(CONFIG_PATH)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    temporary = CONFIG_PATH + '.tmp'
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(descriptor, 'w') as target:
        json.dump(config, target)
    os.replace(temporary, CONFIG_PATH)
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _load_config():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH) as source:
            config = json.load(source)
    except (OSError, json.JSONDecodeError) as exc:
        raise TidyCalError('The local TidyCal credential file cannot be read.') from exc
    if not all(config.get(key) for key in ('client_id', 'access_token', 'refresh_token', 'token_endpoint')):
        raise TidyCalError('The local TidyCal credential file is incomplete. Run the login command again.')
    return config


def _authorization_metadata():
    resource, _ = _request_json(RESOURCE_METADATA_URL)
    authorization_servers = resource.get('authorization_servers') or []
    metadata_url = AUTH_METADATA_URL
    if authorization_servers:
        issuer = authorization_servers[0].rstrip('/')
        if urllib.parse.urlparse(issuer).hostname not in ('tidycal.com', 'www.tidycal.com'):
            raise TidyCalError('TidyCal supplied an unexpected OAuth issuer.')
        metadata_url = issuer + '/.well-known/oauth-authorization-server'
    metadata, _ = _request_json(metadata_url)
    required = ('authorization_endpoint', 'token_endpoint')
    if not all(metadata.get(key) for key in required):
        raise TidyCalError('TidyCal OAuth metadata is missing required endpoints.')
    return resource, metadata


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/callback':
            self.send_error(404)
            return
        self.server.query = urllib.parse.parse_qs(parsed.query)
        body = b'TidyCal authorization received. You can close this tab.'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def login():
    resource, metadata = _authorization_metadata()
    client_data, _ = _request_json(REGISTRATION_URL, {
        'client_name': 'AI OS Dashboard',
        'redirect_uris': [REDIRECT_URI],
        'grant_types': ['authorization_code', 'refresh_token'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'none',
        'scope': SCOPE,
    })
    client_id = client_data.get('client_id')
    if not client_id:
        raise TidyCalError('TidyCal did not return a client ID during registration.')

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': SCOPE,
        'state': state,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'resource': resource.get('resource', MCP_URL),
    }
    authorization_url = metadata['authorization_endpoint'] + '?' + urllib.parse.urlencode(params)
    callback = http.server.HTTPServer(('127.0.0.1', 8765), _CallbackHandler)
    callback.timeout = 240
    print('Opening TidyCal sign-in. Approve read-only scheduling access in your browser.')
    print(authorization_url)
    if not webbrowser.open(authorization_url):
        print('Open the URL above to continue.')
    callback.handle_request()
    query = getattr(callback, 'query', {})
    callback.server_close()
    if query.get('state', [None])[0] != state:
        raise TidyCalError('OAuth state did not match or the sign-in timed out.')
    if query.get('error'):
        raise TidyCalError('TidyCal authorization was not completed.')
    code = query.get('code', [None])[0]
    if not code:
        raise TidyCalError('TidyCal did not return an authorization code.')

    tokens, _ = _request_json(metadata['token_endpoint'], {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': client_id,
        'code_verifier': verifier,
        'resource': resource.get('resource', MCP_URL),
    })
    if not tokens.get('access_token') or not tokens.get('refresh_token'):
        raise TidyCalError('TidyCal did not return the required OAuth tokens.')
    _save_config({
        'client_id': client_id,
        'token_endpoint': metadata['token_endpoint'],
        'resource': resource.get('resource', MCP_URL),
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'expires_at': time.time() + int(tokens.get('expires_in', 3600)),
    })
    print(f'TidyCal credentials saved with owner-only permissions in {CONFIG_PATH}')


def _access_token(config):
    if config.get('expires_at', 0) > time.time() + 60:
        return config['access_token']
    refreshed, _ = _request_json(config['token_endpoint'], {
        'grant_type': 'refresh_token',
        'refresh_token': config['refresh_token'],
        'client_id': config['client_id'],
    })
    if not refreshed.get('access_token'):
        raise TidyCalError('TidyCal could not refresh the OAuth access token. Run login again.')
    config['access_token'] = refreshed['access_token']
    config['refresh_token'] = refreshed.get('refresh_token', config['refresh_token'])
    config['expires_at'] = time.time() + int(refreshed.get('expires_in', 3600))
    _save_config(config)
    return config['access_token']


def _mcp_response(response):
    raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise TidyCalError('TidyCal MCP response exceeded the 2 MB limit.')
    content_type = response.headers.get('Content-Type', '')
    if 'text/event-stream' in content_type:
        data_lines = [line[6:] for line in raw.decode().splitlines() if line.startswith('data: ')]
        if not data_lines:
            return {}, response.headers
        raw = data_lines[-1].encode()
    try:
        return json.loads(raw.decode()), response.headers
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TidyCalError('TidyCal MCP returned an invalid response.') from exc


def _call_tools(config, calls):
    token = _access_token(config)
    headers = {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json, text/event-stream',
        'Content-Type': 'application/json',
        'User-Agent': USER_AGENT,
    }
    next_id = 1

    def send(method, params=None, notification=False):
        nonlocal next_id
        message = {'jsonrpc': '2.0', 'method': method}
        if not notification:
            message['id'] = next_id
            next_id += 1
        if params is not None:
            message['params'] = params
        request = urllib.request.Request(MCP_URL, data=json.dumps(message).encode(), headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_headers = response.headers
                if notification:
                    payload = {}
                else:
                    payload, response_headers = _mcp_response(response)
        except Exception as exc:
            raise TidyCalError(f'TidyCal MCP request failed: {exc}') from exc
        session_id = response_headers.get('Mcp-Session-Id')
        if session_id:
            headers['Mcp-Session-Id'] = session_id
        if payload.get('error'):
            raise TidyCalError(payload['error'].get('message', 'TidyCal MCP returned an error.'))
        return payload.get('result', {})

    send('initialize', {
        'protocolVersion': '2025-03-26',
        'capabilities': {},
        'clientInfo': {'name': 'AI OS Dashboard', 'version': '1.0.0'},
    })
    send('notifications/initialized', notification=True)
    results = {}
    for name, arguments in calls:
        result = send('tools/call', {'name': name, 'arguments': arguments})
        if result.get('isError'):
            text = ' '.join(item.get('text', '') for item in result.get('content', []))
            raise TidyCalError(text or f'TidyCal tool {name} failed.')
        results[name] = result
    return results


def _structured(result):
    if isinstance(result.get('structuredContent'), dict):
        return result['structuredContent']
    for item in result.get('content', []):
        if item.get('type') == 'text':
            try:
                parsed = json.loads(item.get('text', ''))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                if 'TidyCal Pro is required' in item.get('text', ''):
                    raise TidyCalError('TidyCal Pro is required to use the scheduling connection.')
    return {}


def _list_from(result, keys):
    data = _structured(result)
    if isinstance(data, list):
        return data
    for key in keys:
        if isinstance(data.get(key), list):
            return data[key]
    return []


def _booking_type(booking):
    booking_type = booking.get('booking_type') or booking.get('bookingType') or {}
    if isinstance(booking_type, dict):
        return booking_type.get('title') or booking_type.get('name') or 'Meeting'
    return booking_type or 'Meeting'


def dashboard_data():
    """Return a privacy-minimized snapshot for the dashboard, cached for five minutes."""
    if _CACHE['data'] is not None and _CACHE['expires'] > time.time():
        return _CACHE['data']
    try:
        config = _load_config()
        if config is None:
            data = {'configured': False, 'connected': False, 'bookings': [], 'bookingTypes': [],
                    'detail': 'Connect TidyCal with: python3 scripts/tidycal_mcp.py login'}
        else:
            now = datetime.now(timezone.utc)
            calls = [
                ('get-current-user', {}),
                ('list-bookings', {
                    'starts_at': now.isoformat(timespec='seconds'),
                    'ends_at': (now + timedelta(days=30)).isoformat(timespec='seconds'),
                }),
                ('list-booking-types', {}),
            ]
            results = _call_tools(config, calls)
            bookings = _list_from(results['list-bookings'], ('bookings', 'data', 'items', 'results'))
            booking_types = _list_from(results['list-booking-types'], ('booking_types', 'bookingTypes', 'data', 'items', 'results'))
            safe_bookings = [{
                'title': _booking_type(item),
                'startsAt': item.get('starts_at') or item.get('startsAt') or item.get('start_at') or '',
                'endsAt': item.get('ends_at') or item.get('endsAt') or item.get('end_at') or '',
                'status': item.get('status') or 'confirmed',
            } for item in bookings]
            safe_types = [{
                'title': item.get('title') or item.get('name') or 'Booking type',
                'duration': item.get('duration') or item.get('duration_minutes') or '',
            } for item in booking_types]
            data = {'configured': True, 'connected': True, 'bookings': safe_bookings,
                    'bookingTypes': safe_types, 'detail': ''}
    except TidyCalError as exc:
        detail = str(exc)
        if 'TidyCal Pro is required' not in detail:
            print(f'[tidycal] {detail}', file=sys.stderr)
            detail = 'TidyCal could not be reached. Check the dashboard server log.'
        data = {'configured': True, 'connected': False, 'bookings': [], 'bookingTypes': [], 'detail': detail}
    _CACHE.update({'data': data, 'expires': time.time() + (300 if data.get('connected') else 60)})
    return data


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] != 'login':
        print('Usage: python3 scripts/tidycal_mcp.py login')
        raise SystemExit(2)
    try:
        login()
    except TidyCalError as exc:
        print(f'TidyCal login failed: {exc}', file=sys.stderr)
        raise SystemExit(1)

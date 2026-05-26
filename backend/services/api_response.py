from flask import jsonify


def api_success(data=None, message=None, status_code=200, **extra):
    payload = {"success": True, "message": message, "data": data, "error": None}
    payload.update(extra)
    if isinstance(data, dict):
        payload.update(data)
    return jsonify(payload), status_code


def api_error(message, status_code=400, error=None, **extra):
    payload = {"success": False, "message": message, "data": None, "error": error or message}
    payload.update(extra)
    return jsonify(payload), status_code

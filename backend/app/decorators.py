from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

# Attempt to import specific exceptions from flask_jwt_extended.
try:
    from flask_jwt_extended import NoAuthorizationError, InvalidHeaderError
    FLASK_JWT_SPECIFIC_EXCEPTIONS = (NoAuthorizationError, InvalidHeaderError)
except ImportError:
    FLASK_JWT_SPECIFIC_EXCEPTIONS = ()

# PyJWTError is for errors from the underlying PyJWT library.
try:
    # For PyJWT >= 2.0.0, PyJWTError is in jwt.exceptions
    # For older versions, it might be directly under jwt
    from jwt.exceptions import PyJWTError
except ImportError:
    try:
        from jwt import PyJWTError # Fallback for older PyJWT versions
    except ImportError:
        PyJWTError = () # If neither works, use fallback for now
        print("DEBUG: PyJWTError could not be imported, using fallback.") # ADDED_LOG

def _log_decorator_details(fn_name, decorator_name, FLASK_JWT_EXCEPTIONS_EMPTY, PYJWT_ERROR_EMPTY):
    print(f"DEBUG: {decorator_name} for {fn_name}. FLASK_JWT_SPECIFIC_EXCEPTIONS is empty: {FLASK_JWT_EXCEPTIONS_EMPTY}, PyJWTError is empty: {PYJWT_ERROR_EMPTY}")

def _log_verification_attempt():
    print("DEBUG: Attempting verify_jwt_in_request()")

def _log_verification_success(payload):
    print("DEBUG: verify_jwt_in_request() successful.")
    print(f"DEBUG: JWT payload: {payload}")

def _log_exception(e_type, e_str, exception_category="generic"):
    print(f"DEBUG: Caught {exception_category} Exception: {e_type} - {e_str}")

def _log_identity_issue(message):
    print(f"DEBUG: {message}")

def _log_identity_checks(enabled, permission):
    print(f"DEBUG: Identity checks: enabled={enabled}, permission='{permission}'")

def _log_permission_denied(decorator_name, required_permission, user_permission):
    print(f"DEBUG: {decorator_name} permission check failed. Required: '{required_permission}', User: '{user_permission}'")

def _log_all_checks_passed(decorator_name, fn_name):
    print(f"DEBUG: All checks passed for {decorator_name} on {fn_name}.")

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _log_decorator_details(fn.__name__, "admin_required", not FLASK_JWT_SPECIFIC_EXCEPTIONS, not PyJWTError)
        jwt_payload = None
        try:
            _log_verification_attempt()
            verify_jwt_in_request()
            jwt_payload = get_jwt()
            _log_verification_success(jwt_payload)
        except FLASK_JWT_SPECIFIC_EXCEPTIONS as e:
            _log_exception(type(e).__name__, str(e), "FLASK_JWT_SPECIFIC")
            return jsonify(message=f"JWT Authorization Error: {str(e)}"), 401
        except PyJWTError as e:
            _log_exception(type(e).__name__, str(e), "PyJWTError")
            return jsonify(message=f"JWT Token Error: {str(e)}"), 401
        except Exception as e:
            _log_exception(type(e).__name__, str(e))
            return jsonify(message=f"Authentication Error: {str(e)}"), 401

        if not jwt_payload:
            _log_identity_issue("No JWT payload found after try-except block.")
            return jsonify(message="Invalid token or token missing"), 401
        
        user_enabled = jwt_payload.get('enabled')
        user_permission = jwt_payload.get('permission')
        _log_identity_checks(user_enabled, user_permission)

        if not user_enabled:
            _log_identity_issue("Account disabled check failed.")
            return jsonify(message="Error: Account disabled"), 403
        if user_permission != 'admin':
            _log_permission_denied("admin_required", "admin", user_permission)
            return jsonify(message="Forbidden: Admin access required"), 403
        
        _log_all_checks_passed("admin_required", fn.__name__)
        return fn(*args, **kwargs)
    return wrapper

def editor_or_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _log_decorator_details(fn.__name__, "editor_or_admin_required", not FLASK_JWT_SPECIFIC_EXCEPTIONS, not PyJWTError)
        jwt_payload = None
        try:
            _log_verification_attempt()
            verify_jwt_in_request()
            jwt_payload = get_jwt()
            _log_verification_success(jwt_payload)
        except FLASK_JWT_SPECIFIC_EXCEPTIONS as e:
            _log_exception(type(e).__name__, str(e), "FLASK_JWT_SPECIFIC")
            return jsonify(message=f"JWT Authorization Error: {str(e)}"), 401
        except PyJWTError as e:
            _log_exception(type(e).__name__, str(e), "PyJWTError")
            return jsonify(message=f"JWT Token Error: {str(e)}"), 401
        except Exception as e:
            _log_exception(type(e).__name__, str(e))
            return jsonify(message=f"Authentication Error: {str(e)}"), 401

        if not jwt_payload:
            _log_identity_issue("No JWT payload found after try-except block.")
            return jsonify(message="Invalid token or token missing"), 401
        
        user_enabled = jwt_payload.get('enabled')
        user_permission = jwt_payload.get('permission')
        _log_identity_checks(user_enabled, user_permission)

        if not user_enabled:
            _log_identity_issue("Account disabled check failed.")
            return jsonify(message="Error: Account disabled"), 403
        if user_permission not in ['editor', 'admin']:
            _log_permission_denied("editor_or_admin_required", "editor or admin", user_permission)
            return jsonify(message="Forbidden: Editor or Admin access required"), 403
        
        _log_all_checks_passed("editor_or_admin_required", fn.__name__)
        return fn(*args, **kwargs)
    return wrapper

def readonly_or_higher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _log_decorator_details(fn.__name__, "readonly_or_higher_required", not FLASK_JWT_SPECIFIC_EXCEPTIONS, not PyJWTError)
        jwt_payload = None
        try:
            _log_verification_attempt()
            verify_jwt_in_request()
            jwt_payload = get_jwt()
            _log_verification_success(jwt_payload)
        except FLASK_JWT_SPECIFIC_EXCEPTIONS as e:
            _log_exception(type(e).__name__, str(e), "FLASK_JWT_SPECIFIC")
            return jsonify(message=f"JWT Authorization Error: {str(e)}"), 401
        except PyJWTError as e:
            _log_exception(type(e).__name__, str(e), "PyJWTError")
            return jsonify(message=f"JWT Token Error: {str(e)}"), 401
        except Exception as e:
            _log_exception(type(e).__name__, str(e))
            return jsonify(message=f"Authentication Error: {str(e)}"), 401

        if not jwt_payload:
            _log_identity_issue("No JWT payload found after try-except block.")
            return jsonify(message="Invalid token or token missing"), 401
        
        user_enabled = jwt_payload.get('enabled')
        user_permission = jwt_payload.get('permission')
        _log_identity_checks(user_enabled, user_permission)

        if not user_enabled:
            _log_identity_issue("Account disabled check failed.")
            return jsonify(message="Error: Account disabled"), 403
        if user_permission not in ['readonly', 'editor', 'admin']:
            _log_permission_denied("readonly_or_higher_required", "readonly, editor, or admin", user_permission)
            return jsonify(message="Forbidden: Access denied"), 403
        
        _log_all_checks_passed("readonly_or_higher_required", fn.__name__)
        return fn(*args, **kwargs)
    return wrapper

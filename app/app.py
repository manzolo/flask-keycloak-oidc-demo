from flask import Flask, redirect, request, session, url_for, render_template
from functools import wraps
import requests
import os
import base64
import json
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AUTH_SERVER_INTERNAL = os.environ.get('AUTH_SERVER_INTERNAL')
AUTH_SERVER_PUBLIC = os.environ.get('AUTH_SERVER_PUBLIC')
REDIRECT_URI = 'http://localhost:5000/callback'
POST_LOGOUT_REDIRECT_URI = 'http://localhost:5000/' 
RESOURCE_SERVER_INTERNAL_URL = 'http://resource_server:5001' 

app = Flask(__name__)
app.secret_key = 'supersecret' # Use a strong, random key in production!

# Verify that environment variables are loaded
if not all([CLIENT_ID, CLIENT_SECRET, AUTH_SERVER_INTERNAL, AUTH_SERVER_PUBLIC]):
    print("ERROR: Environment variables CLIENT_ID, CLIENT_SECRET, AUTH_SERVER_INTERNAL or AUTH_SERVER_PUBLIC are not set.")
    exit(1)

def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def decode_jwt(token):
    """Decodes the payload of a JWT without signature validation."""
    try:
        parts = token.split('.')
        if len(parts) < 2:
            raise ValueError("Invalid JWT token: less than two parts.")
        payload = parts[1]
        # Adjust padding for base64url decoding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding token: {e}")
        raise

@app.route('/callback')
def callback():
    """Handles the callback from Keycloak after authentication."""
    code = request.args.get('code')
    if not code:
        return f"Error: Authorization code not received. Parameters: {request.args}", 400

    token_url = f"{AUTH_SERVER_INTERNAL}/protocol/openid-connect/token"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    # print(f"Requesting token from: {token_url}") # Debug: verbose
    # print(f"Token request data: {data}") # Debug: verbose
    
    try:
        resp = requests.post(token_url, data=data, timeout=30)
        # print(f"Token response status: {resp.status_code}") # Debug: verbose
        # print(f"Token response headers: {dict(resp.headers)}") # Debug: verbose
        
        if not resp.ok:
            print(f"Token error response: {resp.text}") # Keep for error diagnosis
            return f"Error at token endpoint: {resp.status_code} - {resp.text}", 500

        tokens = resp.json()
        # print(f"Tokens received from Keycloak: {json.dumps(tokens, indent=2)}") # Debug: verbose
        
        access_token = tokens.get('access_token')
        id_token = tokens.get('id_token')
        
        if not access_token:
            return "Access token not received from token endpoint", 500

        # Debugging ID Token presence and decoding
        if id_token:
            # print(f"ID Token received: {id_token[:50]}...{id_token[-20:] if len(id_token) > 50 else ''}") # Debug: verbose
            try:
                decoded_id_token = decode_jwt(id_token)
                # print(f"Decoded ID Token payload: {json.dumps(decoded_id_token, indent=2)}") # Debug: verbose
            except Exception as e:
                print(f"WARNING: Error decoding ID token: {e}") # Keep for warning
        else:
            print("ID Token was NOT received in the token response.") # Keep for warning


        # Debugging Access Token (optional, remove in production)
        # print(f"Access token length: {len(access_token)}")
        # print(f"Access token start: {access_token[:20]}...")
        # print(f"Access token end: ...{access_token[-20:]}")

        # Try to decode access token for debug (optional, remove in production)
        try:
            decoded_access_token = decode_jwt(access_token)
            # print(f"Access Token decoded successfully.")
            # print(f"Access Token subject: {decoded_access_token.get('sub')}")
            # print(f"Access Token issuer: {decoded_access_token.get('iss')}")
            # print(f"Access Token audience: {decoded_access_token.get('aud')}")
            # print(f"Access Token expiry: {decoded_access_token.get('exp')}")
        except Exception as e:
            print(f"Warning: Could not decode access token: {e}") # Keep for warning

        access_token = access_token.strip()

        # Request userinfo
        userinfo_url = f"{AUTH_SERVER_INTERNAL}/protocol/openid-connect/userinfo"
        # print(f"Requesting userinfo from: {userinfo_url}") # Debug: verbose
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        # print(f"Userinfo request headers: {headers}") # Debug: verbose
        
        userinfo_resp = requests.get(
            userinfo_url,
            headers=headers,
            timeout=30
        )
        
        # print(f"Userinfo response status: {userinfo_resp.status_code}") # Debug: verbose
        # print(f"Userinfo response headers: {dict(userinfo_resp.headers)}") # Debug: verbose
        
        if not userinfo_resp.ok:
            print(f"Userinfo error response: {userinfo_resp.text}") # Keep for error diagnosis
            
            # Try alternative approach: extract user info from ID token if available
            if id_token:
                print("Attempting to extract userinfo from ID token as fallback...") # Keep for info
                try:
                    userinfo = decode_jwt(id_token)
                    session['user'] = userinfo.get('preferred_username') or userinfo.get('sub')
                    session['userinfo'] = userinfo
                    session['access_token'] = access_token
                    session['id_token'] = id_token # Save ID Token to session
                    print(f"Successfully extracted userinfo from ID token: {session['user']}") # Keep for info
                    return redirect(url_for('index'))
                except Exception as e:
                    print(f"Failed to decode ID token for fallback: {e}") # Keep for error diagnosis
            
            return f"Error at userinfo endpoint: {userinfo_resp.status_code} - {userinfo_resp.text}", 500

        userinfo = userinfo_resp.json()
        # print(f"Userinfo received: {userinfo}") # Debug: verbose
        
        session['user'] = userinfo.get('preferred_username')
        session['userinfo'] = userinfo
        session['access_token'] = access_token
        session['id_token'] = id_token # Save ID Token to session

        return redirect(url_for('index'))
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}") # Keep for error diagnosis
        return f"Connection error: {e}", 500
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}") # Keep for error diagnosis
        return f"JSON decoding error: {e}", 500
    
@app.route('/token')
@login_required
def show_token():
    """Displays the decoded content of the access token."""
    access_token = session.get('access_token')
    if not access_token:
        return "Access token not available in session.", 404
    try:
        decoded = decode_jwt(access_token)
        return render_template('token.html', token=decoded)
    except Exception as e:
        return f"Error decoding token: {e}", 500

@app.route('/')
def index():
    """Home page."""
    return render_template("index.html", user=session.get('user'))

@app.route('/login')
def login():
    """Redirects to Keycloak for authentication."""
    # print(f"Redirecting for login to: {AUTH_SERVER_PUBLIC}/protocol/openid-connect/auth") # Debug: verbose
    return redirect(
        f"{AUTH_SERVER_PUBLIC}/protocol/openid-connect/auth"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid profile"
        f"&redirect_uri={REDIRECT_URI}"
    )

@app.route('/logout', methods=['POST'])
def logout():
    """Performs logout by clearing Flask session and disconnecting from Keycloak."""
    id_token = session.get('id_token')
    # print(f"ID Token from session before clear: {id_token}") # Debug: verbose
    
    # Clear Flask session immediately
    session.clear() 

    # Build Keycloak logout URL
    logout_url = (
        f"{AUTH_SERVER_PUBLIC}/protocol/openid-connect/logout"
        f"?post_logout_redirect_uri={POST_LOGOUT_REDIRECT_URI}"
    )

    # Add id_token_hint if available for a more robust logout
    if id_token:
        logout_url += f"&id_token_hint={id_token}"
    else:
        print("WARNING: id_token_hint not available for federated logout. Logout might not terminate Keycloak session.") # Keep for warning
    
    # print(f"Redirecting for logout to Keycloak: {logout_url}") # Debug: verbose
    return redirect(logout_url)

@app.route('/profile')
@login_required
def profile():
    """Displays user profile information."""
    return render_template('profile.html', user=session.get('user'), info=session.get('userinfo'))

@app.route('/call-protected-api')
@login_required
def call_protected_api():
    """
    Makes a call to the protected resource server using the access token.
    """
    access_token = session.get('access_token')
    if not access_token:
        return "Access token not found in session. Please log in.", 401

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(f"{RESOURCE_SERVER_INTERNAL_URL}/protected-resource", headers=headers, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        
        api_response_data = response.json()
        return render_template('api_response.html', api_response=api_response_data)

    except requests.exceptions.RequestException as e:
        error_message = f"Error calling protected API: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f" - Status: {e.response.status_code}, Response: {e.response.text}"
        print(error_message)
        return f"Failed to call protected API: {error_message}", 500
    except json.JSONDecodeError as e:
        print(f"JSON decode error from API response: {e}")
        return f"Error decoding API response: {e}", 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


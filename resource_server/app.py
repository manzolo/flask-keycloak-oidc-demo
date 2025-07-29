from flask import Flask, request, jsonify
import os
import requests
from jose import jwt, jwk
from jose.exceptions import JWTError, JWTClaimsError, JWKError

app = Flask(__name__)

# Keycloak internal URL for JWKS endpoint
# This should match the internal Keycloak service name in docker-compose.yml
KEYCLOAK_JWKS_URL = 'http://keycloak:8080/realms/myrealm/protocol/openid-connect/certs'
# Expected issuer from Keycloak's ID Token or Access Token
KEYCLOAK_ISSUER = 'http://localhost:8080/realms/myrealm'
# Expected audience for the access token (this is usually the client_id of the resource server itself,
# but for simplicity in this demo, we'll use the client_id of the Flask app if the token's audience
# is set to it, or you might configure a specific audience for the resource server in Keycloak)
# For this demo, we'll assume the access token's audience is 'my-client' (the Flask app's client ID)
# or that the resource server itself is part of the audience if configured in Keycloak.
# In a real-world scenario, you might have a dedicated client for the resource server in Keycloak
# and use its client_id as the audience here.
EXPECTED_AUDIENCE = 'my-client' 

# Cache for Keycloak's public keys
# In a production environment, you would want to refresh this periodically
# and handle key rotation.
_cached_jwks = None

def get_keycloak_jwks():
    """Fetches Keycloak's JSON Web Key Set (JWKS)."""
    global _cached_jwks
    if _cached_jwks is None:
        try:
            print(f"Fetching JWKS from: {KEYCLOAK_JWKS_URL}")
            response = requests.get(KEYCLOAK_JWKS_URL, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors
            _cached_jwks = response.json()
            print("JWKS fetched successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching JWKS: {e}")
            raise ConnectionError(f"Could not fetch JWKS from Keycloak: {e}")
    return _cached_jwks

def validate_token(token):
    """
    Validates a JWT token against Keycloak's public keys and checks claims.
    Returns the decoded payload if valid, raises an exception otherwise.
    """
    jwks = get_keycloak_jwks()
    
    try:
        # Decode and verify the token
        # audience: The expected audience of the token. Can be a string or a list of strings.
        # issuer: The expected issuer of the token.
        # algorithms: The allowed algorithms for the token signature.
        # options: 'verify_at_hash' is important if 'at_hash' claim is present in ID Token
        #          and you want to verify it against the access token. Not strictly needed for access tokens.
        decoded_token = jwt.decode(
            token,
            jwks,
            audience=EXPECTED_AUDIENCE,
            issuer=KEYCLOAK_ISSUER,
            algorithms=["RS256"], # Keycloak typically uses RS256 for signing
            options={"verify_at_hash": False} # Set to True if verifying ID Token with at_hash
        )
        return decoded_token
    except JWTClaimsError as e:
        print(f"JWT Claims Error: {e}")
        raise ValueError(f"Token claims invalid: {e}")
    except JWTError as e:
        print(f"JWT Verification Error: {e}")
        raise ValueError(f"Token verification failed: {e}")
    except JWKError as e:
        print(f"JWK Error: {e}")
        raise ValueError(f"JWK error during token verification: {e}")
    except Exception as e:
        print(f"Unexpected error during token validation: {e}")
        raise ValueError(f"Token validation failed due to unexpected error: {e}")

@app.route('/protected-resource', methods=['GET'])
def protected_resource():
    """
    This endpoint requires a valid Bearer token in the Authorization header.
    It performs full JWT validation.
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"message": "Authorization header missing"}), 401

    if not auth_header.startswith('Bearer '):
        return jsonify({"message": "Invalid Authorization header format. Expected 'Bearer <token>'"}), 401

    access_token = auth_header.split(' ')[1]

    try:
        # Validate the token
        decoded_payload = validate_token(access_token)
        
        # If validation succeeds, you can use the information from the decoded_payload
        # For example, to get the user ID:
        user_id = decoded_payload.get('sub', 'unknown')
        preferred_username = decoded_payload.get('preferred_username', 'unknown')

        # Simulate fetching some protected data
        protected_data = {
            "message": "This is highly confidential data from the protected resource!",
            "received_token_length": len(access_token),
            "accessed_by_user_id": user_id,
            "preferred_username": preferred_username,
            "token_claims": decoded_payload # Include decoded claims for demo purposes
        }
        return jsonify(protected_data), 200
    except ValueError as e:
        # Token validation failed
        return jsonify({"message": f"Unauthorized: {e}"}), 401
    except ConnectionError as e:
        # JWKS fetching failed
        return jsonify({"message": f"Server error: Could not connect to Keycloak for token validation: {e}"}), 500
    except Exception as e:
        # General unexpected error
        print(f"An unexpected error occurred in protected_resource: {e}")
        return jsonify({"message": "An internal server error occurred."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "Resource Server is healthy"}), 200

if __name__ == "__main__":
    # The resource server will run on port 5001 inside its container
    app.run(host="0.0.0.0", port=5001, debug=True)
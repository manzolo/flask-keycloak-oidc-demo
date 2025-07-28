# Flask Keycloak OIDC Demo

This project demonstrates a complete Flask web application integrated with Keycloak for OpenID Connect (OIDC) authentication. It showcases secure user login, profile management, token handling, and federated logout using a fully containerized environment with Docker Compose.

## 🚀 Features

- **🔐 Secure Authentication**: Implements OAuth 2.0 Authorization Code Flow with PKCE via Keycloak
- **👤 User Profile Management**: Fetches and displays comprehensive user information from Keycloak's userinfo endpoint
- **🎫 JWT Token Handling**: Demonstrates access token management and JWT payload inspection
- **🚪 Federated Logout**: Properly logs out users from both the Flask application and Keycloak IDP
- **🐳 Fully Dockerized**: Runs Keycloak and Flask app in isolated Docker containers with proper networking
- **🎨 Modern UI**: Clean, responsive interface built with Tailwind CSS
- **📊 Debug Dashboard**: Built-in token inspector and user information viewer
- **🔄 Auto-Import Realm**: Automatically configures Keycloak realm and test users on startup

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Git** for cloning the repository

## 🛠️ Project Structure

```
flask-keycloak-oidc-demo/
├── app/
│   ├── app.py                 # Main Flask application
│   ├── Dockerfile            # Flask app container configuration
│   ├── .env                  # Environment variables
│   └── templates/            # HTML templates
│       ├── index.html
│       ├── token.html
│       └── profile.html
├── keycloak/
│   └── realm-export.json     # Keycloak realm configuration
├── docker-compose.yml        # Multi-container orchestration
└── README.md                 # This file
```

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/manzolo/flask-keycloak-oidc-demo.git
cd flask-keycloak-oidc-demo
```

### 2. Check Environment Configuration

Check the environment file for the Flask application:

```bash
# app/.env file
CLIENT_ID=my-client-id
CLIENT_SECRET=secret
AUTH_SERVER_INTERNAL=http://keycloak:8080/realms/myrealm
AUTH_SERVER_PUBLIC=http://localhost:8080/realms/myrealm
```

### 3. Verify Keycloak Realm Configuration

Ensure your `keycloak/realm-export.json` contains the correct configuration:

```json
{
  "realm": "myrealm",
  "enabled": true,
  "clients": [
    {
      "clientId": "my-client-id",
      "enabled": true,
      "protocol": "openid-connect",
      "publicClient": false,
      "secret": "secret",
      "redirectUris": [
        "http://localhost:5000/callback"
      ],
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "authorizationServicesEnabled": false,
      "baseUrl": "http://localhost:5000",
      "webOrigins": [
        "+"
      ]
    }
  ],
  "users": [
    {
      "username": "manzolo",
      "email": "manzolo@keycloak.org",
      "firstName": "Andrea",
      "lastName": "Manzi",
      "enabled": true,
      "emailVerified": true,
      "credentials": [
        {
          "type": "password",
          "value": "password",
          "temporary": false
        }
      ]
    }
  ]
}
```

### 4. Build and Run the Application

Navigate to the project root directory and execute:

```bash
# Stop any existing containers
docker-compose down

# Build fresh images (ignore cache to pick up all changes)
docker-compose build --no-cache

# Start all services
docker-compose up
```

**What this does:**
- 🏗️ Builds Docker images for both Keycloak and the Flask application
- 🚀 Starts Keycloak with automatic realm import
- 🌐 Launches the Flask application with proper network connectivity
- 📝 Creates isolated networks for secure container communication

### 5. Verify Services are Running

Check that both services are healthy:

```bash
# Check container status
docker-compose ps

# View logs for troubleshooting
docker-compose logs -f

# Check individual service logs
docker-compose logs keycloak
docker-compose logs app
```

## 🎯 Usage Guide

### Basic Authentication Flow

1. **Access the Application**
   - Open your browser and navigate to `http://localhost:5000`
   - You'll see the welcome page with login options

2. **Authenticate with Keycloak**
   - Click the **"Login"** button
   - You'll be redirected to Keycloak's authentication page
   - Use the test credentials:
     - **Username**: `manzolo`
     - **Password**: `password`

3. **Explore Authenticated Features**
   - After successful login, you'll see a personalized welcome message
   - Click **"Show Profile"** to view detailed user information
   - Click **"Show Token"** to inspect the JWT access token payload

4. **Logout Process**
   - Click **"Logout"** to terminate the session
   - This will log you out from both the Flask app and Keycloak
   - You'll be redirected back to the home page

### Available Endpoints

| Endpoint | Description | Authentication Required |
|----------|-------------|------------------------|
| `/` | Home page | No |
| `/login` | Initiate OIDC login flow | No |
| `/callback` | OAuth callback handler | No |
| `/profile` | User profile information | Yes |
| `/token` | JWT token inspector | Yes |
| `/logout` | Federated logout | Yes |

## 🔧 Configuration Details

### Environment Variables

The Flask application uses the following environment variables (defined in `app/.env`):

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `CLIENT_ID` | Keycloak OIDC client identifier | `my-client-id` |
| `CLIENT_SECRET` | Client secret for authentication | `secret` |
| `AUTH_SERVER_INTERNAL` | Internal Keycloak URL (container-to-container) | `http://keycloak:8080/realms/myrealm` |
| `AUTH_SERVER_PUBLIC` | Public Keycloak URL (browser-accessible) | `http://localhost:8080/realms/myrealm` |

### Keycloak Configuration

- **Admin Console**: `http://localhost:8080/admin`
  - Username: `admin`
  - Password: `admin`
- **Realm**: `myrealm`
- **Client ID**: `my-client-id`
- **Supported Flows**: Authorization Code, Direct Access Grants

## 🐛 Troubleshooting

### Common Issues and Solutions

1. **Login fails with "invalid_user_credentials"**
   ```bash
   # Check if the realm was imported correctly
   docker-compose logs keycloak | grep -i import
   
   # Verify user exists in Keycloak admin console
   # Navigate to: http://localhost:8080/admin -> Users
   ```

2. **UserInfo request fails with "invalid_token"**
   ```bash
   # Check token format and network connectivity
   docker-compose logs app | grep -i token
   
   # Verify client configuration in Keycloak
   # Ensure "Full Scope Allowed" is enabled
   ```

3. **Connection refused errors**
   ```bash
   # Ensure services are running
   docker-compose ps
   
   # Check network connectivity
   docker-compose exec app ping keycloak
   ```

4. **Port conflicts**
   ```bash
   # If ports 5000 or 8080 are in use, modify docker-compose.yml
   # Change the port mappings to available ports
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy coding! 🎉**
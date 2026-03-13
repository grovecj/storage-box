# Google OAuth Setup

This document explains how to configure Google OAuth for the Storage Boxes application.

## Development Mode (No OAuth)

If `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are not configured, the app runs in **development mode**:

- A "Dev Login" button appears on the login page
- Clicking it auto-logs you in as a test user
- No Google OAuth is required
- Perfect for local development

## Production Mode (With OAuth)

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (or People API)

### 2. Configure OAuth Consent Screen

1. Navigate to **APIs & Services > OAuth consent screen**
2. Choose **External** user type
3. Fill in:
   - App name: Storage Boxes
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `openid`
   - `email`
   - `profile`
5. Add test users if app is in testing mode

### 3. Create OAuth Credentials

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Application type: **Web application**
4. Name: Storage Boxes
5. Add **Authorized redirect URIs**:
   - For local dev: `http://localhost/api/v1/auth/google/callback`
   - For production: `https://boxes.cartergrove.me/api/v1/auth/google/callback`
6. Click **Create**
7. Copy the **Client ID** and **Client secret**

### 4. Configure Environment Variables

#### Local Development (docker-compose)

Create a `.env` file in the project root:

```bash
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

Restart the services:

```bash
docker compose down
docker compose up -d --build
```

#### Production (DigitalOcean)

Update your Terraform variables:

```bash
# In terraform.tfvars or via command line
google_client_id     = "your-client-id-here.apps.googleusercontent.com"
google_client_secret = "your-client-secret-here"
```

Apply the Terraform changes:

```bash
cd terraform
terraform apply
```

Or set via DigitalOcean App Platform console:
1. Go to your app in DigitalOcean
2. Settings > Environment Variables
3. Add `GOOGLE_CLIENT_ID` (encrypted)
4. Add `GOOGLE_CLIENT_SECRET` (encrypted)
5. Redeploy

## OAuth Flow

1. User clicks "Sign in with Google" on `/login`
2. App redirects to Google OAuth consent screen
3. User authorizes the app
4. Google redirects back to `/api/v1/auth/google/callback` with authorization code
5. Backend exchanges code for user info
6. Backend creates or updates user in database
7. Backend generates JWT token
8. Backend redirects to frontend `/auth/callback?token=<jwt>`
9. Frontend stores token in localStorage
10. Frontend redirects to dashboard

## Security Notes

- JWT tokens expire after 7 days (configurable via `JWT_EXPIRATION_MINUTES`)
- Tokens are stored in localStorage (client-side)
- All API requests include `Authorization: Bearer <token>` header
- 401 responses automatically redirect to login
- Sign out clears token from localStorage
- All data is scoped to the authenticated user's `owner_id`

## Troubleshooting

### "Dev token only available in dev mode" error

This means OAuth is configured. Either:
- Use "Sign in with Google" button
- Remove `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to use dev mode

### "Invalid authentication credentials" on API calls

- Check that token is present in localStorage
- Check that token hasn't expired
- Try logging out and back in

### "Redirect URI mismatch" error

- Ensure the redirect URI in Google Console exactly matches your callback URL
- Include the full path: `/api/v1/auth/google/callback`
- Match the protocol (http vs https) and domain

### Users can't see each other's data

This is expected! Each user has isolated boxes and items based on their `owner_id`.

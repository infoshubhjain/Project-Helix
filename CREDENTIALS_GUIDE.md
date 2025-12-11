# Project Helix - Credentials Setup Guide

This guide provides detailed, step-by-step instructions for obtaining all required API credentials.

---

## 1. Azure AD Credentials (For Outlook Email Import)

These credentials allow the app to read emails from your Microsoft Outlook account.

### Required Values:
- `CLIENT_ID`
- `TENANT_ID`
- `CLIENT_SECRET`

### Step-by-Step Instructions:

#### Step 1: Access Azure Portal
1. Go to https://portal.azure.com/
2. Sign in with your Microsoft account (use your @illinois.edu email or personal Microsoft account)
3. If you don't have an account, create one (it's free)

#### Step 2: Register a New Application
1. In the Azure Portal, search for **"Azure Active Directory"** in the top search bar
2. Click on **"Azure Active Directory"** from the results
3. In the left sidebar, click **"App registrations"**
4. Click **"+ New registration"** at the top

#### Step 3: Configure Application Registration
1. **Name**: Enter a name like `Project Helix Email Parser` or `UIUC Project Helix`
2. **Supported account types**: Select **"Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts"**
   - This allows both university and personal Microsoft accounts
3. **Redirect URI**:
   - Select **"Public client/native (mobile & desktop)"** from the dropdown
   - Enter: `http://localhost`
4. Click **"Register"**

#### Step 4: Get CLIENT_ID and TENANT_ID
After registration, you'll see the "Overview" page:

1. **Copy the CLIENT_ID**:
   - Look for **"Application (client) ID"**
   - It looks like: `12345678-1234-1234-1234-123456789abc`
   - Copy this value → This is your `CLIENT_ID`

2. **Copy the TENANT_ID**:
   - Look for **"Directory (tenant) ID"**
   - It looks like: `87654321-4321-4321-4321-cba987654321`
   - Copy this value → This is your `TENANT_ID`

#### Step 5: Create CLIENT_SECRET
1. In the left sidebar, click **"Certificates & secrets"**
2. Click the **"Client secrets"** tab
3. Click **"+ New client secret"**
4. **Description**: Enter something like `Project Helix Secret`
5. **Expires**: Select **"24 months"** (or your preferred duration)
6. Click **"Add"**
7. **IMPORTANT**: Immediately copy the **"Value"** (not the "Secret ID")
   - It looks like: `abc123~DEF456.GHI789-JKL012_MNO345`
   - **This is shown ONLY ONCE!** If you lose it, you'll need to create a new one
   - Copy this value → This is your `CLIENT_SECRET`

#### Step 6: Add API Permissions
1. In the left sidebar, click **"API permissions"**
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. In the search box, type `Mail.Read`
6. Check the box next to **"Mail.Read"**
7. Click **"Add permissions"** at the bottom
8. (Optional but recommended) Click **"Grant admin consent for [your organization]"** if available

#### Step 7: Enable Public Client Flow
1. In the left sidebar, click **"Authentication"**
2. Scroll down to **"Advanced settings"**
3. Under **"Allow public client flows"**, toggle **"Enable the following mobile and desktop flows"** to **YES**
4. Click **"Save"** at the top

### ✅ What You Should Have Now:
```env
CLIENT_ID=12345678-1234-1234-1234-123456789abc
TENANT_ID=87654321-4321-4321-4321-cba987654321
CLIENT_SECRET=abc123~DEF456.GHI789-JKL012_MNO345
```

---

## 2. OpenRouter API Key (For AI Email Parsing)

This allows the app to use AI to intelligently parse events from email content.

### Required Value:
- `CHAT_KEY`

### Step-by-Step Instructions:

#### Step 1: Create an Account
1. Go to https://openrouter.ai/
2. Click **"Sign In"** in the top right
3. Choose to sign in with:
   - Google account, OR
   - GitHub account, OR
   - Email/password

#### Step 2: Add Credits (Required for API Usage)
1. After signing in, you'll see your dashboard
2. Click your profile icon or username in the top right
3. Click **"Credits"** or **"Add Credits"**
4. OpenRouter uses a pay-as-you-go model:
   - Minimum: $5 (recommended starting amount)
   - The app uses the `openai/gpt-oss-120b` model which is very affordable
   - Typical cost: ~$0.01-0.05 per email parsed
5. Add credits using:
   - Credit card
   - PayPal
   - Cryptocurrency (if available)

#### Step 3: Generate API Key
1. After adding credits, click your profile icon again
2. Click **"API Keys"** or **"Keys"**
3. Click **"+ Create Key"** or **"Generate New Key"**
4. **Name**: Enter something like `Project Helix Parser`
5. **Rate Limit** (optional): Leave blank or set to reasonable limits
6. Click **"Create"**
7. **Copy the API key**:
   - It looks like: `sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`
   - **Store this safely!** You may not be able to see it again
   - Copy this value → This is your `CHAT_KEY`

### ✅ What You Should Have Now:
```env
CHAT_KEY=sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

### Alternative: Use OpenAI Directly
If you prefer to use OpenAI instead of OpenRouter:

1. Go to https://platform.openai.com/
2. Sign in or create an account
3. Click **"API keys"** in the left sidebar
4. Click **"+ Create new secret key"**
5. Name it and copy the key
6. **Important**: You'll also need to modify `Project/calander/readEmail.py`:
   - Line 71: Change `base_url="https://openrouter.ai/api/v1"` to just `OpenAI()` (remove the base_url parameter)
   - Line 76: Change the model to `"gpt-4o-mini"` or `"gpt-4"`

---

## 3. Google Calendar Credentials (Optional but Recommended)

This allows the app to read/write to your Google Calendar and display your personal events.

### Required File:
- `credentials.json` (to be placed in `Project/calander/`)

### Step-by-Step Instructions:

#### Step 1: Access Google Cloud Console
1. Go to https://console.cloud.google.com/
2. Sign in with your Google account (use @gmail.com or @illinois.edu)

#### Step 2: Create a New Project
1. At the top, click the project dropdown (says "Select a project" or shows current project name)
2. Click **"NEW PROJECT"** in the top right of the popup
3. **Project name**: Enter `Project Helix` or `UIUC Calendar App`
4. **Organization**: Leave as "No organization" (unless you have one)
5. Click **"CREATE"**
6. Wait a few seconds for the project to be created
7. Make sure your new project is selected (check the dropdown at the top)

#### Step 3: Enable Google Calendar API
1. In the left sidebar, click **"APIs & Services"** → **"Library"**
   - Or search for "API Library" in the top search bar
2. In the API Library search box, type: `Google Calendar API`
3. Click on **"Google Calendar API"** from the results
4. Click the blue **"ENABLE"** button
5. Wait for it to enable (takes a few seconds)

#### Step 4: Configure OAuth Consent Screen
1. In the left sidebar, click **"OAuth consent screen"**
2. Choose **"External"** user type
3. Click **"CREATE"**
4. Fill in the required fields:
   - **App name**: `Project Helix` or `UIUC Calendar App`
   - **User support email**: Your email address (select from dropdown)
   - **Developer contact information**: Your email address
5. Leave everything else as default
6. Click **"SAVE AND CONTINUE"**
7. On the **"Scopes"** page, click **"ADD OR REMOVE SCOPES"**
8. Search for and select:
   - `https://www.googleapis.com/auth/calendar` (See, edit, share, and permanently delete all the calendars you can access using Google Calendar)
9. Click **"UPDATE"**
10. Click **"SAVE AND CONTINUE"**
11. On **"Test users"** page, click **"+ ADD USERS"**
12. Enter your email address (the one you'll use to test)
13. Click **"ADD"**
14. Click **"SAVE AND CONTINUE"**
15. Review the summary and click **"BACK TO DASHBOARD"**

#### Step 5: Create OAuth 2.0 Credentials
1. In the left sidebar, click **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. **Application type**: Select **"Desktop app"**
5. **Name**: Enter `Project Helix Desktop Client`
6. Click **"CREATE"**
7. A popup will appear saying "OAuth client created"

#### Step 6: Download credentials.json
1. In the popup, click **"DOWNLOAD JSON"**
   - Or click the download icon (⬇️) next to your OAuth 2.0 Client ID in the credentials list
2. The file will download as something like `client_secret_123456789.json`
3. **Rename** this file to `credentials.json`
4. **Move** it to: `/Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json`

#### Step 7: Verify File Location
The file should be at this exact path:
```
/Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
```

### ✅ What Your credentials.json Should Look Like:
```json
{
  "installed": {
    "client_id": "123456789-abc.apps.googleusercontent.com",
    "project_id": "eventflow-123456",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-abc123def456ghi789",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

## 4. Final Configuration

### Add All Credentials to .env File

Open `/Users/shubh/Desktop/Project-Helix/Project/.env` and update it:

```env
# Microsoft Azure AD Credentials (for Outlook email integration)
CLIENT_ID=12345678-1234-1234-1234-123456789abc
TENANT_ID=87654321-4321-4321-4321-cba987654321
CLIENT_SECRET=abc123~DEF456.GHI789-JKL012_MNO345

# OpenAI/OpenRouter API Key (for email parsing)
CHAT_KEY=sk-or-v1-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**Replace the placeholder values with your actual credentials!**

### Verify File Structure

Your project should have:
```
Project-Helix/
└── Project/
    ├── .env                              ← Azure & OpenRouter credentials
    └── calander/
        └── credentials.json              ← Google OAuth credentials
```

---

## 5. Testing Your Credentials

### Test Azure AD (Email Import)
1. Run the app: `./run.sh`
2. Open http://localhost:5000
3. Click **"Add from Email"**
4. Enter number of emails (try 1-5 first)
5. Click **"Process Emails"**
6. A browser window should open asking you to sign in to Microsoft
7. Sign in and grant permissions
8. Events should appear!

### Test OpenRouter (AI Parsing)
- This is tested automatically when you process emails
- Check the terminal for any API errors
- If you see "RAW OUTPUT" in the terminal, it's working!

### Test Google Calendar
1. Click **"Connect Your Google Calendar"** in the top right
2. A Google sign-in popup should appear
3. Sign in with your Google account
4. Grant calendar permissions
5. Your calendar should appear in the iframe!
6. The first time, a `token.json` file will be created in `Project/calander/`

---

## Common Issues & Solutions

### Issue: "Invalid client" error (Azure)
**Solution**:
- Double-check your CLIENT_ID and TENANT_ID
- Make sure you enabled "Public client flows" in Azure
- Verify redirect URI is set to `http://localhost`

### Issue: "API key invalid" error (OpenRouter)
**Solution**:
- Verify you copied the entire key (they're very long)
- Check you have credits in your OpenRouter account
- Make sure there are no extra spaces in the .env file

### Issue: "The OAuth client was not found" (Google)
**Solution**:
- Make sure credentials.json is in the correct location
- Verify the JSON file is valid (open in a text editor)
- Check the OAuth consent screen is configured
- Ensure the Google Calendar API is enabled

### Issue: Environment variables not loading
**Solution**:
- Restart the Flask app after editing .env
- Check for typos in variable names
- Make sure there are no quotes around values in .env
- Verify .env is in the Project/ directory

---

## Security Best Practices

1. **Never commit credentials to Git**
   - The `.gitignore` file already protects `.env` and `credentials.json`
   - Always verify before running `git add`

2. **Rotate secrets regularly**
   - Azure secrets can be rotated in the Azure Portal
   - OpenRouter keys can be regenerated
   - Google credentials can be deleted and recreated

3. **Use minimal permissions**
   - Azure: Only grant `Mail.Read` (already configured)
   - Google: Only grant Calendar access (already configured)

4. **Monitor usage**
   - Check OpenRouter dashboard for API usage
   - Azure shows API calls in the portal
   - Google Cloud Console shows quota usage

---

## Cost Breakdown

### Azure AD
- **Free** for email reading

### OpenRouter
- **Pay as you go** starting from $5
- Estimated cost: $0.01-0.05 per email parsed
- $5 credit = approximately 100-500 emails parsed

### Google Calendar
- **Free** for personal use
- No quota limits for typical student usage

---

## Support & Troubleshooting

If you encounter issues:

1. **Check terminal output** for detailed error messages
2. **Verify credentials** are correctly copied (no extra spaces)
3. **Restart the app** after changing .env
4. **Check API dashboards** for service status
5. **Review the SETUP.md** for additional troubleshooting

---

## Quick Reference

| Credential | Source | Location |
|------------|--------|----------|
| CLIENT_ID | Azure Portal → App registrations | Project/.env |
| TENANT_ID | Azure Portal → App registrations | Project/.env |
| CLIENT_SECRET | Azure Portal → Certificates & secrets | Project/.env |
| CHAT_KEY | OpenRouter.ai → API Keys | Project/.env |
| credentials.json | Google Cloud Console → Credentials | Project/calander/ |

---

**Ready to test?** Start the app with `./run.sh` and try each feature!

# Credentials Quick Summary

## What You Need

```
┌─────────────────────────────────────────────────────────────┐
│                    3 SETS OF CREDENTIALS                     │
└─────────────────────────────────────────────────────────────┘

1️⃣  AZURE AD (Microsoft/Outlook Email Access)
2️⃣  OPENROUTER (AI Email Parsing)
3️⃣  GOOGLE CALENDAR (Calendar Integration) - Optional
```

---

## 1️⃣ Azure AD - Email Import

### What it does:
Reads emails from your Outlook/Microsoft account to find events

### Where to get it:
🔗 https://portal.azure.com/

### Quick Steps:
1. Azure Portal → Azure Active Directory
2. App registrations → New registration
3. Copy **Application (client) ID** → `CLIENT_ID`
4. Copy **Directory (tenant) ID** → `TENANT_ID`
5. Certificates & secrets → New client secret → Copy **Value** → `CLIENT_SECRET`
6. API permissions → Add permission → Microsoft Graph → Mail.Read

### Example values:
```env
CLIENT_ID=a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
TENANT_ID=z9y8x7w6-v5u4-t3s2-r1q0-p9o8n7m6l5k4
CLIENT_SECRET=abc~123.DEF-456_GHI789
```

### Cost: FREE ✅

---

## 2️⃣ OpenRouter - AI Email Parsing

### What it does:
Uses AI to intelligently extract event details from email text

### Where to get it:
🔗 https://openrouter.ai/

### Quick Steps:
1. Sign up/Sign in (use Google or GitHub)
2. Add credits ($5 minimum recommended)
3. Profile → API Keys → Create Key
4. Copy the key → `CHAT_KEY`

### Example value:
```env
CHAT_KEY=sk-or-v1-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ
```

### Cost: ~$0.01-0.05 per email 💵
- $5 = approximately 100-500 emails parsed

### Alternative: OpenAI
- Use https://platform.openai.com/ instead
- Similar pricing
- Need to modify `readEmail.py` (see detailed guide)

---

## 3️⃣ Google Calendar - Calendar Integration (Optional)

### What it does:
Syncs events with your Google Calendar, displays your calendar in the app

### Where to get it:
🔗 https://console.cloud.google.com/

### Quick Steps:
1. Create new project
2. Enable "Google Calendar API"
3. Create OAuth consent screen (External, add your email as test user)
4. Create credentials → OAuth client ID → Desktop app
5. Download JSON file
6. Rename to `credentials.json`
7. Move to: `Project/calander/credentials.json`

### File location:
```
Project/calander/credentials.json
```

### Cost: FREE ✅

---

## Final Setup

### 1. Edit .env file:
**Location**: `/Users/shubh/Desktop/Project-Helix/Project/.env`

```env
# Microsoft Azure AD Credentials
CLIENT_ID=your_client_id_from_azure
TENANT_ID=your_tenant_id_from_azure
CLIENT_SECRET=your_client_secret_from_azure

# OpenRouter API Key
CHAT_KEY=your_openrouter_api_key
```

### 2. Place credentials.json:
**Location**: `/Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json`

### 3. Test:
```bash
./run.sh
```
Open: http://localhost:5000

---

## Testing Each Feature

### ✅ Test Email Import (Azure + OpenRouter)
1. Click "📧 Add from Email"
2. Enter "5" for number of emails
3. Click "Process Emails"
4. Sign in to Microsoft when prompted
5. Events should appear!

### ✅ Test Calendar Sync (Google)
1. Click "🔗 Connect Your Google Calendar"
2. Sign in to Google when prompted
3. Grant calendar permissions
4. Your calendar appears!

### ✅ Test Event Browsing (No credentials needed)
1. Scroll to "Browse Events Near UIUC"
2. Events load from Firebase automatically
3. Search and filter working!

---

## Priority Setup

If you want to start quickly, get them in this order:

### Minimum to run the app:
✅ **None!** - Browse events works without any credentials

### To use email import:
1. ✅ Azure AD (CLIENT_ID, TENANT_ID, CLIENT_SECRET)
2. ✅ OpenRouter (CHAT_KEY)

### To use calendar features:
3. ✅ Google Calendar (credentials.json)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "CLIENT_ID not found" | Check .env is in Project/ folder |
| "Invalid client" | Enable "Public client flows" in Azure |
| "API key invalid" | Verify OpenRouter credits, check for typos |
| "OAuth client not found" | Check credentials.json location & filename |
| Environment vars not loading | Restart Flask app after editing .env |

---

## Need More Help?

📖 **Detailed Guide**: Read [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md)
- Step-by-step screenshots walkthrough
- Detailed explanations for each service
- Common issues and solutions

📖 **Setup Guide**: Read [SETUP.md](SETUP.md)
- Full application setup
- Architecture details
- Running scrapers

📖 **Quick Start**: Read [QUICKSTART.md](QUICKSTART.md)
- 5-minute setup
- First-time configuration

---

## Security Reminders

🔒 **Never commit credentials to Git** - Already protected by .gitignore
🔒 **Don't share credentials** - These are personal API keys
🔒 **Rotate regularly** - Change secrets every few months
🔒 **Monitor usage** - Check dashboards for unexpected activity

---

**Ready?** Get your credentials and let's go! 🚀

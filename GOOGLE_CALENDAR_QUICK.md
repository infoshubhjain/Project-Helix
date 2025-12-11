# Google Calendar - Quick Steps

## ⚡ Super Fast Version

### 1. Google Cloud Console
- Go to: https://console.cloud.google.com/
- Create new project: "Project Helix"
- Enable "Google Calendar API"

### 2. OAuth Consent Screen
- Choose "External"
- Fill in app name: "Project Helix"
- Add scope: `https://www.googleapis.com/auth/calendar`
- Add yourself as test user

### 3. Create Credentials
- Credentials → Create → OAuth client ID
- Type: "Desktop app"
- Download JSON file

### 4. Install Credentials
```bash
# Rename downloaded file to credentials.json
mv ~/Downloads/client_secret_*.json ~/Downloads/credentials.json

# Move to correct location
mv ~/Downloads/credentials.json /Users/shubh/Desktop/Project-Helix/Project/calander/
```

### 5. Connect in App
1. Run: `./run.sh`
2. Open: http://localhost:5001
3. Click: "🔗 Connect Your Google Calendar"
4. Sign in and allow permissions
5. Done! ✅

---

## 🎯 What Each Step Does

| Step | What Happens | Time |
|------|--------------|------|
| 1. Create project | Sets up Google Cloud workspace | 1 min |
| 2. Enable API | Allows calendar access | 30 sec |
| 3. OAuth screen | Tells Google about your app | 2 min |
| 4. Credentials | Downloads the key file | 1 min |
| 5. Move file | Puts key in right place | 30 sec |
| 6. Connect | Links your calendar to app | 1 min |

**Total:** ~6 minutes

---

## 📍 Important URLs

- **Google Cloud Console:** https://console.cloud.google.com/
- **API Library:** https://console.cloud.google.com/apis/library
- **Credentials:** https://console.cloud.google.com/apis/credentials

---

## ✅ Checklist

Use this to track your progress:

- [ ] Visited Google Cloud Console
- [ ] Created project named "Project Helix"
- [ ] Enabled Google Calendar API
- [ ] Configured OAuth consent screen
- [ ] Added myself as test user
- [ ] Created OAuth client ID (Desktop app)
- [ ] Downloaded credentials JSON file
- [ ] Renamed file to `credentials.json`
- [ ] Moved to `Project/calander/credentials.json`
- [ ] Restarted app
- [ ] Clicked "Connect Your Google Calendar"
- [ ] Signed in and allowed permissions
- [ ] Saw "✅ Connected" message

---

## 🚨 Common Mistakes

### ❌ Wrong Application Type
- **Wrong:** "Web application"
- **Right:** "Desktop app"

### ❌ Wrong File Location
- **Wrong:** `Project/credentials.json`
- **Right:** `Project/calander/credentials.json`

### ❌ Wrong File Name
- **Wrong:** `client_secret_123.json`
- **Right:** `credentials.json`

### ❌ API Not Enabled
- Must enable "Google Calendar API"
- Not just "Google Calendar"

---

## 🔍 Verify Setup

Check each file exists:

```bash
# Check credentials.json
ls -la /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json

# Should output:
# -rw-r--r--  1 shubh  staff  [size] [date] credentials.json
```

After connecting:
```bash
# Check token.json was created
ls -la /Users/shubh/Desktop/Project-Helix/Project/calander/token.json

# Should output:
# -rw-r--r--  1 shubh  staff  [size] [date] token.json
```

---

## 🎓 Video Tutorial Alternative

If you prefer visual guides:

1. YouTube: Search "Google Calendar API Python OAuth"
2. Google Docs: [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)

The process is the same, just ignore their Python code - you already have it!

---

## 💡 Pro Tips

1. **Use your university email** if you want university calendar events
2. **Use personal Gmail** if you want personal calendar
3. **You can connect multiple accounts** by deleting token.json and reconnecting
4. **Don't delete credentials.json** - you only download it once
5. **Token.json can be deleted** - it will be recreated when you reconnect

---

## 🆘 Need More Detail?

Read the full guide: **[GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)**

It has:
- Screenshots descriptions
- Detailed troubleshooting
- Security explanations
- FAQ section

---

## 📞 Quick Help

### Error: "OAuth client not found"
→ Check file is at: `Project/calander/credentials.json`

### Error: "This app isn't verified"
→ Click "Advanced" → "Go to Project Helix (unsafe)"
→ This is normal for your own app!

### Calendar not showing
→ Refresh browser
→ Check browser console (F12)

### Want to disconnect
→ Delete `Project/calander/token.json`

---

**Time:** 6 minutes
**Cost:** FREE
**Difficulty:** Easy

**Let's do it!** 🚀

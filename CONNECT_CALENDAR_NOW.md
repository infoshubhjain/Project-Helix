# ✅ Ready to Connect Your Google Calendar!

## 🎉 Your credentials.json is installed correctly!

### File Details:
- ✅ Location: `Project/calander/credentials.json`
- ✅ Valid JSON structure
- ✅ Client ID: 691968245686-jqj22uc...
- ✅ Project: plated-life-480911-g4

---

## 🚀 Now Connect Your Calendar (3 Steps):

### Step 1: Start the App
Open Terminal and run:
```bash
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```

You should see:
```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  Access the application at: http://localhost:5001      ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

 * Running on http://127.0.0.1:5001
```

---

### Step 2: Open in Browser
Open your browser to:
```
http://localhost:5001
```

---

### Step 3: Connect Your Calendar

1. **Look at the TOP-RIGHT corner** of the page

2. **Click the button:** "🔗 Connect Your Google Calendar"

3. **A browser window will open** asking you to:
   - Choose your Google account
   - Click on the account you want to use

4. **You'll see a warning:** "Google hasn't verified this app"
   - **This is NORMAL!** It's your own app
   - Click **"Advanced"** (small text at bottom-left)
   - Click **"Go to plated-life-480911-g4 (unsafe)"**

5. **Grant permissions:**
   - Google will ask to access your calendar
   - Click **"Continue"** or **"Allow"**

6. **Success!** 🎉
   - You'll be redirected back to the app
   - The button will change to: "✅ Connected as your-email@gmail.com"
   - Your calendar will appear in the iframe!

---

## 🎯 What You'll See After Connecting:

### "Your Calendar" Section:
- Your actual Google Calendar embedded in the app
- Navigate months with arrow buttons
- See all your personal events

### "Upcoming Events" Section:
- Today's agenda from your calendar
- See what's coming up

### "Browse Events" Section:
- Still shows 1000+ campus events
- You can now add them to your Google Calendar

---

## ⚠️ Important Notes:

### The "unverified app" warning is NORMAL
- This appears for all personal projects
- Your app is running locally on YOUR computer
- No one else can access it
- It's completely safe to proceed

### What to click:
1. "Advanced" (bottom-left of warning page)
2. "Go to plated-life-480911-g4 (unsafe)"
3. "Allow" (on permissions page)

---

## 🔧 Troubleshooting:

### If the "Connect" button doesn't appear:
- Make sure you're at http://localhost:5001
- Refresh the page (Cmd+R or F5)
- Check browser console (F12) for errors

### If clicking the button does nothing:
- Check browser console (F12 → Console tab)
- Make sure credentials.json is still in place:
  ```bash
  ls -la /Users/shubh/Desktop/Project-Helix/Project/calander/credentials.json
  ```

### If you get "redirect_uri_mismatch" error:
- Go back to Google Cloud Console
- Credentials → Edit your OAuth client
- Make sure redirect URI includes: `http://localhost`

### To reconnect with different account:
```bash
# Delete the token file
rm /Users/shubh/Desktop/Project-Helix/Project/calander/token.json

# Restart app and connect again
./run.sh
```

---

## 📁 Files to Expect:

### Before Connecting:
```
Project/calander/credentials.json  ✅ (you have this)
```

### After Connecting:
```
Project/calander/credentials.json  ✅
Project/calander/token.json        ✅ (will be created)
```

The `token.json` file stores your login session so you don't have to reconnect every time.

---

## 🎓 Quick Test:

1. Start app: `./run.sh`
2. Open: http://localhost:5001
3. Click "🔗 Connect Your Google Calendar"
4. Sign in and allow
5. See your calendar appear!

---

## ✨ You're Almost There!

Just run:
```bash
./run.sh
```

Then click the "Connect" button in the top-right corner of the app!

---

**Need help?** The connection process takes about 30 seconds. Just follow the prompts!

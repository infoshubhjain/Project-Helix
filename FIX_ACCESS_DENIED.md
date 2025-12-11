# Fix: Error 403 - access_denied

## 🔍 What Happened:
Your OAuth app is in "Testing" mode, which means only approved test users can sign in. You need to add **sj9827205802@gmail.com** as a test user.

## ✅ Quick Fix (2 minutes):

### Step 1: Open OAuth Consent Screen
Go to: **https://console.cloud.google.com/apis/credentials/consent**

Make sure your project **"plated-life-480911-g4"** is selected at the top.

---

### Step 2: Add Test User

1. On the OAuth consent screen page, look for the **"Test users"** section
   - It should be in the middle or bottom of the page

2. Click **"+ ADD USERS"** button

3. In the popup, enter your email:
   ```
   sj9827205802@gmail.com
   ```

4. Click **"ADD"** or **"SAVE"**

---

### Step 3: Verify Test User Added

You should now see your email listed under "Test users":
```
Test users
sj9827205802@gmail.com
```

---

### Step 4: Try Connecting Again

1. Go back to your app: **http://localhost:5001**
2. Refresh the page (Cmd+R or F5)
3. Click **"🔗 Connect Your Google Calendar"** again
4. Sign in with **sj9827205802@gmail.com**
5. You'll still see "Google hasn't verified this app" warning - **this is normal!**
   - Click **"Advanced"** (bottom left)
   - Click **"Go to plated-life-480911-g4 (unsafe)"**
6. Click **"Continue"** to allow calendar access
7. **Done!** ✅

---

## 🎯 Visual Guide:

### What You're Looking For:

```
╔════════════════════════════════════════════╗
║ OAuth consent screen                       ║
╠════════════════════════════════════════════╣
║                                            ║
║ App information                            ║
║ ├─ App name: plated-life-480911-g4        ║
║ ├─ User support email: ...                ║
║ └─ ...                                     ║
║                                            ║
║ Scopes                                     ║
║ └─ .../auth/calendar                      ║
║                                            ║
║ Test users                    [+ ADD USERS]║  <-- CLICK HERE
║ └─ sj9827205802@gmail.com    (after add)  ║
║                                            ║
╚════════════════════════════════════════════╝
```

---

## ⚠️ Why This Happened:

When you create an OAuth app, Google puts it in **"Testing"** mode by default:
- ✅ **Testing mode**: Only specific test users can sign in
- 🚫 **Production mode**: Anyone can sign in (requires Google verification - takes weeks)

For personal projects, **Testing mode is perfect!** Just add yourself as a test user.

---

## 🆘 Can't Find "Add Users" Button?

### Option A: Via Edit App
1. Click **"EDIT APP"** button (top of page)
2. Navigate through the steps using "SAVE AND CONTINUE"
3. On **Step 3: "Test users"**, click **"+ ADD USERS"**
4. Enter: `sj9827205802@gmail.com`
5. Click "ADD"
6. Click "SAVE AND CONTINUE" to the end

### Option B: Direct Link
Try this direct link:
https://console.cloud.google.com/apis/credentials/consent/edit

Then scroll to "Test users" section.

---

## 📋 Quick Commands:

```bash
# Open Google Cloud Console OAuth page
open https://console.cloud.google.com/apis/credentials/consent

# After adding test user, restart your app
cd /Users/shubh/Desktop/Project-Helix
./run.sh
```

---

## ✅ Success Checklist:

- [ ] Opened OAuth consent screen page
- [ ] Found "Test users" section
- [ ] Clicked "+ ADD USERS"
- [ ] Entered `sj9827205802@gmail.com`
- [ ] Clicked "ADD" or "SAVE"
- [ ] Saw email appear in test users list
- [ ] Refreshed app at http://localhost:5001
- [ ] Clicked "Connect Your Google Calendar"
- [ ] Clicked "Advanced" → "Go to ... (unsafe)"
- [ ] Allowed calendar permissions
- [ ] Saw "✅ Connected" message

---

**This should take 2 minutes max!** Try it and let me know if you see the test users section!

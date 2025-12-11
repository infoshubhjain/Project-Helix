# Fix: Error 400 - redirect_uri_mismatch

## 🔍 What's Happening:
Google is blocking your login because the redirect URI from your site doesn't match what's authorized in Google Cloud Console.

## ✅ Solution: Add Your GitHub Pages URL to Google Cloud Console

### Step 1: Go to Google Cloud Console Credentials
Open this URL:
```
https://console.cloud.google.com/apis/credentials
```

Make sure **"plated-life-480911-g4"** project is selected at the top.

### Step 2: Find Your OAuth 2.0 Client ID
Look for your OAuth client:
- **Name**: Something like "Web client 1" or your custom name
- **Client ID**: `691968245686-5cdnqs5inasr62td91id893m70lg3k09.apps.googleusercontent.com`

Click on it to edit.

### Step 3: Add Authorized JavaScript Origins
In the **"Authorized JavaScript origins"** section, click **"+ ADD URI"** and add:

```
https://infoshubhjain.github.io
```

**Important**:
- ✅ NO trailing slash
- ✅ Use `https://` (not `http://`)
- ✅ Just the domain, no path

### Step 4: Add Authorized Redirect URIs
In the **"Authorized redirect URIs"** section, click **"+ ADD URI"** and add these:

```
https://infoshubhjain.github.io/Project-Helix/
https://infoshubhjain.github.io/Project-Helix
https://infoshubhjain.github.io
```

**Also keep your localhost URIs for testing:**
```
http://localhost:5001
http://127.0.0.1:5001
http://localhost:5001/
http://127.0.0.1:5001/
```

### Step 5: Save Changes
Click the **"SAVE"** button at the bottom of the page.

## 🎯 Expected Result

Your configuration should look like this:

### Authorized JavaScript origins:
```
✅ https://infoshubhjain.github.io
✅ http://localhost:5001
✅ http://127.0.0.1:5001
```

### Authorized redirect URIs:
```
✅ https://infoshubhjain.github.io/Project-Helix/
✅ https://infoshubhjain.github.io/Project-Helix
✅ https://infoshubhjain.github.io
✅ http://localhost:5001
✅ http://127.0.0.1:5001
✅ http://localhost:5001/
✅ http://127.0.0.1:5001/
```

## 🧪 Test It

1. **Save** your changes in Google Cloud Console
2. **Wait 1-2 minutes** for Google to propagate the changes
3. **Go to your site**: https://infoshubhjain.github.io/Project-Helix/
4. **Hard refresh**: Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
5. **Click** "Connect Your Google Calendar"
6. **Sign in** - should work now! ✅

## 🔍 Still Getting the Error?

### Double-Check These:

1. **Correct Project Selected?**
   - Make sure you're editing the right Google Cloud project
   - Check the project name at the top of the page

2. **Exact URL Match?**
   - GitHub Pages URL must be EXACTLY: `https://infoshubhjain.github.io`
   - No `www.`, no trailing slash on the origin
   - WITH trailing slash on redirect URIs

3. **Saved Changes?**
   - Click the "SAVE" button at the bottom
   - Look for green success message

4. **Wait a Moment**
   - Google OAuth changes can take 1-2 minutes to propagate
   - Clear your browser cache if needed

## 📋 Complete Checklist

- [ ] Opened Google Cloud Console credentials page
- [ ] Found OAuth 2.0 Client ID (`691968245686...`)
- [ ] Added `https://infoshubhjain.github.io` to JavaScript origins
- [ ] Added redirect URIs:
  - [ ] `https://infoshubhjain.github.io/Project-Helix/`
  - [ ] `https://infoshubhjain.github.io/Project-Helix`
  - [ ] `https://infoshubhjain.github.io`
- [ ] Kept localhost URIs for local testing
- [ ] Clicked "SAVE" button
- [ ] Waited 1-2 minutes
- [ ] Hard refreshed the page (Cmd+Shift+R)
- [ ] Tried connecting again

## 🎓 Why This Happens

Google OAuth requires you to pre-register every domain/URL that can request authentication. This is a security measure to prevent malicious sites from stealing your credentials.

When you:
- Deploy to GitHub Pages → New domain → Must add to OAuth config
- Test locally → Different domain → Must add localhost too

## 🆘 Advanced Troubleshooting

### See the Exact Error Details:

1. **Open Browser Console** (F12 or Cmd+Option+I)
2. **Go to Console tab**
3. **Click "Connect Your Google Calendar"**
4. **Look for error message** - it will show the exact redirect URI that failed

The error will look like:
```
Request Details
redirect_uri=https://infoshubhjain.github.io/Project-Helix/
```

Copy that EXACT URI and add it to Google Cloud Console.

### Verify Your Current Config:

Run this in browser console on your site:
```javascript
console.log('Current origin:', window.location.origin);
console.log('Current pathname:', window.location.pathname);
console.log('Full URL:', window.location.href);
```

Add whatever it prints as the origin to your Google Cloud Console.

## ✅ Quick Fix Commands

**Current site URL:**
```
https://infoshubhjain.github.io/Project-Helix/
```

**Add to Google Cloud Console:**
- **JavaScript origin**: `https://infoshubhjain.github.io`
- **Redirect URI**: `https://infoshubhjain.github.io/Project-Helix/`

---

**After adding these URIs and saving, wait 1-2 minutes and try again!**

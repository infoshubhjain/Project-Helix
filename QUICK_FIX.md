# 🚨 QUICK FIX - Error 400: redirect_uri_mismatch

## ⚡ 3-Minute Fix

### 1️⃣ Open Google Cloud Console (1 minute)
Click this link:
```
https://console.cloud.google.com/apis/credentials?project=plated-life-480911-g4
```

### 2️⃣ Edit Your OAuth Client (1 minute)
- Click on the OAuth 2.0 Client ID: `691968245686-5cdnqs5inasr62td91id893m70lg3k09`
- Scroll to **"Authorized JavaScript origins"**
- Click **"+ ADD URI"**
- Paste: `https://infoshubhjain.github.io`
- Click **"+ ADD URI"** again under **"Authorized redirect URIs"**
- Paste: `https://infoshubhjain.github.io/Project-Helix/`
- Click **SAVE** at the bottom

### 3️⃣ Test (1 minute)
- Wait 1 minute for Google to update
- Go to: https://infoshubhjain.github.io/Project-Helix/
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Click "Connect Your Google Calendar"
- ✅ Should work!

---

## 📸 What It Should Look Like

### Authorized JavaScript origins:
```
https://infoshubhjain.github.io
http://localhost:5001
http://127.0.0.1:5001
```

### Authorized redirect URIs:
```
https://infoshubhjain.github.io/Project-Helix/
https://infoshubhjain.github.io/Project-Helix
http://localhost:5001
http://127.0.0.1:5001
```

---

## ❓ Still Not Working?

1. **Did you click SAVE?** (Bottom of the page)
2. **Wait 2 minutes** after saving
3. **Clear browser cache**: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)
4. **Try incognito mode**: Cmd+Shift+N (Mac) or Ctrl+Shift+N (Windows)

---

**Need more help?** See [FIX_REDIRECT_URI_ERROR.md](FIX_REDIRECT_URI_ERROR.md) for detailed instructions.

# 🚀 Deploy EventFlow to GitHub Pages

This guide will help you deploy your EventFlow app to GitHub Pages so it's accessible at `https://infoshubhjain.github.io/Project-Helix/`

## 📋 Prerequisites

- GitHub account (you already have this: infoshubhjain)
- Git repository (already set up: Project-Helix)
- Google OAuth credentials (already configured)

## 🔧 Step 1: Update Google OAuth Redirect URIs

Since you're hosting on GitHub Pages, you need to add your GitHub Pages URL to the authorized redirect URIs in Google Cloud Console.

### 1.1 Go to Google Cloud Console
```
https://console.cloud.google.com/apis/credentials
```

### 1.2 Find Your OAuth Client ID
- Look for: `691968245686-5cdnqs5inasr62td91id893m70lg3k09.apps.googleusercontent.com`
- Click on it to edit

### 1.3 Add Authorized JavaScript Origins
Add these URLs:
```
https://infoshubhjain.github.io
http://localhost:5001
http://127.0.0.1:5001
```

### 1.4 Add Authorized Redirect URIs
Add these URLs:
```
https://infoshubhjain.github.io/Project-Helix/
https://infoshubhjain.github.io/Project-Helix
http://localhost:5001
http://127.0.0.1:5001
```

### 1.5 Save Changes
Click **"SAVE"** at the bottom

## 📤 Step 2: Commit and Push Changes

```bash
# Add all changes
git add .

# Commit with a descriptive message
git commit -m "Add GitHub Pages support with persistent Google Calendar auth

- Created static index.html for GitHub Pages deployment
- Implemented token persistence using localStorage
- Added automatic silent token refresh (55 min intervals)
- Enhanced session management for indefinite authentication
- Updated calendar connection to work without Flask backend"

# Push to GitHub
git push origin main
```

## ⚙️ Step 3: Enable GitHub Pages

### 3.1 Go to Your Repository Settings
```
https://github.com/infoshubhjain/Project-Helix/settings/pages
```

### 3.2 Configure GitHub Pages
1. **Source**: Select `Deploy from a branch`
2. **Branch**: Select `main`
3. **Folder**: Select `/ (root)`
4. Click **"Save"**

### 3.3 Wait for Deployment
GitHub will build and deploy your site. This takes 2-5 minutes.

You'll see a message like:
```
✅ Your site is live at https://infoshubhjain.github.io/Project-Helix/
```

## 🌐 Step 4: Access Your Live Site

Once deployed, visit:
```
https://infoshubhjain.github.io/Project-Helix/
```

## ✅ Step 5: Test the Live Site

1. **Open the URL** in your browser
2. **Click "Connect Your Google Calendar"**
3. **Sign in** with your Google account
4. **Verify** the calendar loads
5. **Refresh the page** - you should stay connected!
6. **Test auto-refresh** - wait 55 minutes to see silent token refresh

## 🔍 Troubleshooting

### Issue: "Error 400: redirect_uri_mismatch"
**Fix**: Make sure you added the GitHub Pages URL to authorized redirect URIs in Google Cloud Console

### Issue: "Calendar not loading"
**Fix**:
1. Check browser console (F12) for errors
2. Verify Google Calendar API is enabled in Google Cloud Console
3. Confirm API key and Client ID are correct in `index.html`

### Issue: "Changes not showing up"
**Fix**:
1. Wait 2-5 minutes for GitHub Pages to rebuild
2. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Clear browser cache

### Issue: "Token not persisting"
**Fix**:
1. Check browser console for localStorage errors
2. Ensure cookies/localStorage are enabled in browser
3. Try incognito/private mode to test fresh

## 📊 Monitoring Deployment Status

Check deployment status at:
```
https://github.com/infoshubhjain/Project-Helix/deployments
```

You can see:
- ✅ Active deployments
- 🔄 In-progress builds
- ❌ Failed builds (with error logs)

## 🔄 Making Updates

After making changes to your code:

```bash
# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push (triggers automatic rebuild)
git push origin main
```

GitHub Pages will automatically rebuild and deploy within 2-5 minutes.

## 🎯 What's Included

### ✅ Working Features
- Google Calendar integration with OAuth
- Persistent authentication (localStorage)
- Automatic token refresh every 55 minutes
- Calendar view with month navigation
- Event browsing and search
- Add events to Google Calendar
- Responsive design

### ⚠️ Disabled Features (Static Site Limitations)
- Email parsing (requires backend server)
  - Can be re-enabled using serverless functions (Vercel, Netlify, etc.)

## 🚀 Alternative Deployment Options

If you need the email parsing feature, consider these platforms that support Flask:

### Option 1: Vercel (Recommended for Flask)
- Free tier available
- Supports Python backends
- Easy deployment: `vercel deploy`
- Custom domains

### Option 2: Render
- Free tier available
- Full Flask support
- Auto-deploys from GitHub
- Link: https://render.com

### Option 3: Railway
- Free tier available ($5 credit/month)
- Full Flask support
- Link: https://railway.app

## 📝 Notes

- **GitHub Pages is free** and perfect for static sites
- **No server costs** - everything runs in the browser
- **Automatic HTTPS** - GitHub provides SSL certificates
- **Fast CDN** - GitHub's global CDN ensures fast loading
- **Token security** - Tokens stored in browser localStorage (per-domain)

## 🆘 Need Help?

If you encounter issues:
1. Check browser console (F12) for detailed error messages
2. Review GitHub Actions logs in your repository
3. Verify all URLs in Google Cloud Console are correct
4. Test locally first: `python Project/app.py` → http://localhost:5001

---

**🎉 Your site will be live at:** `https://infoshubhjain.github.io/Project-Helix/`

**📧 Questions?** Check the browser console or GitHub deployment logs for detailed error information.

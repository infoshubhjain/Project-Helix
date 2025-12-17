# 🌙 Dark Mode Toggle Button - User Guide

## ✅ Dark Mode Button Added to Header!

A prominent dark mode toggle button has been added to the **top-right corner** of your website for easy access.

---

## 📍 Where to Find It

### Location 1: Header (NEW - Most Prominent)
The dark mode button is now in the **header**, right next to your Google Calendar connection button.

```
┌─────────────────────────────────────────────────────┐
│  🏛️ Project Helix @ Illinois          🔗 Calendar  🌙 │
└─────────────────────────────────────────────────────┘
                                                    ↑
                                          Dark Mode Button Here!
```

**Features:**
- 🟠 **Orange background** in light mode (🌙 moon icon)
- 🟡 **Gold/yellow background** in dark mode (☀️ sun icon)
- Always visible at the top of the page
- Smooth hover animation

### Location 2: Browse Events Section (Original)
There's also a dark mode button in the Browse Events section (with the export buttons).

```
Browse Events Near UIUC     [Search] [Filter ▼] [📅 iCal] [📊 CSV] [🌙]
                                                                    ↑
                                                  Also works here!
```

**Both buttons work the same way and stay in sync!**

---

## 🎨 How It Looks

### Light Mode (Default)
- **Header Button**: 🌙 on orange background
- **Text**: White
- **Hover**: Brighter orange + lifts up

### Dark Mode (After Click)
- **Header Button**: ☀️ on gold background
- **Text**: White
- **Hover**: Lighter gold + lifts up

---

## 🔄 How to Use

### Toggle Dark Mode
1. **Click the 🌙 button** in the header (top-right)
2. Page instantly switches to dark theme
3. Button changes to ☀️
4. Toast notification confirms the change

### Return to Light Mode
1. **Click the ☀️ button** (now in dark mode)
2. Page switches back to light theme
3. Button changes back to 🌙

**Your preference is automatically saved!** It will persist when you:
- Refresh the page
- Close and reopen the browser
- Visit from another tab

---

## ⚡ Features

### Auto-Save Preference
- ✅ Saves to browser localStorage
- ✅ Remembers your choice forever
- ✅ Works across multiple tabs

### System Preference Detection
- ✅ Detects if your OS is in dark mode
- ✅ Automatically applies dark theme on first visit
- ✅ Manual toggle overrides system preference

### Toast Notifications
- ✅ Shows "Dark Mode On" when enabled
- ✅ Shows "Light Mode On" when disabled
- ✅ Auto-dismisses after 2 seconds

---

## 🎯 Testing

After the changes deploy (1-3 minutes), test it:

1. **Visit**: https://infoshubhjain.github.io/Project-Helix/
2. **Hard refresh**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. **Look top-right**: You should see the 🌙 button
4. **Click it**: Page switches to dark mode
5. **Button changes**: From 🌙 to ☀️
6. **Refresh page**: Dark mode should persist

---

## 🌓 What Changes in Dark Mode

When you activate dark mode, everything changes:

### Background
- Navy blue gradient (instead of Illinois blue)
- Dark slate cards (instead of white)

### Text
- Light gray text (instead of dark blue)
- High contrast for readability

### Buttons & UI
- Adjusted colors for dark theme
- Export buttons adapt
- Modals use dark background
- Inputs use dark styling

### Same Great Features
- ✅ All buttons still work
- ✅ Export still functions
- ✅ Calendar still loads
- ✅ Search/filter still work

---

## 📱 Mobile & Desktop

The button works on all devices:
- ✅ Desktop browsers
- ✅ Mobile phones
- ✅ Tablets
- ✅ All screen sizes

On mobile, the button might wrap to a second line in the header, but it's still easily accessible.

---

## 🔧 Technical Details

### Button IDs
- Header button: `id="dark-mode-toggle-header"`
- Browse button: `id="dark-mode-toggle"`

Both trigger the same function: `toggleDarkMode()`

### CSS Classes
- `.dark-mode-btn-header` - Header button styling
- `.dark-mode-btn` - Browse section button styling
- `body.dark-mode` - Applied when dark mode is active

### JavaScript Function
```javascript
function toggleDarkMode() {
  // Toggles dark mode
  // Updates both buttons
  // Shows toast notification
  // Saves preference
}
```

---

## 🎨 Customization

If you want to customize the button appearance, edit:

**File**: `/Project/static/style.css`

**Lines**: 1135-1166

```css
.dark-mode-btn-header {
  background: var(--primary-dark);  /* Change button color */
  font-size: 18px;                   /* Change icon size */
  padding: 10px 16px;                /* Change button size */
}
```

---

## ✅ Summary

**Where**: Top-right corner of header
**Icon**: 🌙 (light mode) / ☀️ (dark mode)
**Color**: Orange (light) / Gold (dark)
**Action**: Click to toggle
**State**: Auto-saved

**Deployed**: Commit 7bfb354
**Status**: ✅ Live on GitHub Pages

---

## 📝 Changelog

### Version 2.0.1 (2025-12-17)
- ✨ Added prominent dark mode button in header
- 🎨 Orange/gold styling for better visibility
- 🔄 Synchronized with browse section button
- 💾 Preference auto-saves to localStorage

**Enjoy your new dark mode toggle!** 🌙✨

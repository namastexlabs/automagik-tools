# WorkOS AuthKit Branding Guide - Automagik Tools Hub

## Overview

This guide provides complete, ready-to-paste configuration for branding your WorkOS AuthKit login pages to match the Automagik Tools Hub purple gradient aesthetic.

**Estimated Time**: 75 minutes
**Result**: Beautiful, branded login experience with animated gradients and floating orbs

---

## Prerequisites

- Access to WorkOS Dashboard: https://dashboard.workos.com/
- Navigate to: **Production → Branding**
- Have your logo assets ready (or use placeholders)

---

## Step 1: Upload Assets (15 minutes)

### Required Assets

1. **Logo** (full wordmark):
   - Minimum: 160x160px
   - Formats: JPG, PNG, or SVG
   - Max size: 100KB
   - Example: Automagik Tools full logo with text

2. **Logo Icon** (square/logomark):
   - Minimum: 160x160px
   - Aspect ratio: 1:1
   - Formats: JPG, PNG, or SVG
   - Max size: 100KB
   - Example: Square "A" logomark

3. **Favicon**:
   - Minimum: 32x32px
   - Aspect ratio: 1:1
   - Formats: JPG, PNG, GIF, SVG, WebP, AVIF, or ICO
   - Max size: 100KB

### Upload Instructions

1. Go to **Assets** section in the branding editor
2. Click **Upload** for each asset type
3. Select your files
4. Choose logo style (full logo vs icon) by clicking the logo in the preview

---

## Step 2: Configure Colors (10 minutes)

### Light Mode

```
Page background: #ffffff
Button background: #8b5cf6
Button text: #ffffff
Link color: #8b5cf6
```

### Dark Mode

```
Page background: #0f172a
Button background: #a78bfa
Button text: #ffffff
Link color: #c4b5fd
```

### Appearance Settings

- **Corner radius**: `8px`
- **Theme preference**: Allow OS system settings

---

## Step 3: Configure Page Settings (5 minutes)

### Links

- **Privacy policy**: `https://namastex.ai/privacy`
- **Terms of service**: `https://namastex.ai/terms`

### User Information

- ✅ **Require first name**: Enabled
- ✅ **Require last name**: Enabled

### Copy (Page Title)

Click on the page title in the preview and change to:
```
Welcome to Automagik Tools Hub
```

### Alternate Action Link

- Sign-in page: "Need an account?"
- Sign-up page: "Already have an account?"

---

## Step 4: Enable Split Layout (2 minutes)

1. Select **Page Layout** section
2. Choose **Split layout** (two columns)
3. Position: **Right** (secondary panel on right side)
4. **Hide on mobile**: Disabled (show on all devices)

---

## Step 5: Add Custom HTML/CSS Panel (30 minutes)

### 5.1 Click on Secondary Column

Click the secondary column in the preview pane to open the custom code dialog.

### 5.2 Paste HTML

Copy and paste this entire HTML block into the **HTML editor**:

```html
<div class="custom-panel">
  <div class="hero-section">
    <div class="icon-badge">
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke-width="2"/>
      </svg>
    </div>
    <h1>Automagik Tools Hub</h1>
    <p class="tagline">Your intelligent MCP assistant</p>
  </div>

  <div class="features">
    <div class="feature-card">
      <div class="feature-icon">⚡</div>
      <h3>Instant Generation</h3>
      <p>Transform any API into MCP tools in seconds</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🧠</div>
      <h3>Self-Learning</h3>
      <p>Continuously improves from every interaction</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🔌</div>
      <h3>Universal</h3>
      <p>Works with Claude, Cursor, and any MCP client</p>
    </div>
  </div>

  <div class="footer">
    <p>Powered by <strong>Namastex Labs</strong></p>
  </div>
</div>
```

### 5.3 Paste CSS

Copy and paste this entire CSS block into the **CSS editor**:

```css
.custom-panel {
  position: relative;
  min-height: 100%;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

/* Animated background orbs */
.custom-panel::before,
.custom-panel::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
  animation: float 20s ease-in-out infinite;
}

.custom-panel::before {
  width: 400px;
  height: 400px;
  background: #8b5cf6;
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.custom-panel::after {
  width: 300px;
  height: 300px;
  background: #3b82f6;
  bottom: -100px;
  right: -100px;
  animation-delay: 10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(30px, -30px); }
  66% { transform: translate(-20px, 20px); }
}

.hero-section {
  position: relative;
  z-index: 1;
  text-align: center;
  margin-bottom: 3rem;
}

.icon-badge {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  width: 40px;
  height: 40px;
  color: white;
}

.hero-section h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.tagline {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.features {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 1.5rem;
  width: 100%;
  max-width: 400px;
  margin-bottom: 3rem;
}

.feature-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.feature-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
  margin: 0 0 0.5rem;
}

.feature-card p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.5;
}

.footer {
  position: relative;
  z-index: 1;
  text-align: center;
}

.footer p {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.footer strong {
  color: white;
  font-weight: 600;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .custom-panel {
    padding: 2rem 1rem;
  }

  .hero-section h1 {
    font-size: 2rem;
  }

  .features {
    gap: 1rem;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .custom-panel {
    background: linear-gradient(135deg, #4c1d95 0%, #312e81 100%);
  }
}
```

### 5.4 Preview

The preview should now show:
- ✅ Animated purple gradient background
- ✅ Floating blur orbs
- ✅ Icon badge with lightning bolt
- ✅ Hero heading and tagline
- ✅ Three feature cards with hover effects
- ✅ Footer with Namastex Labs branding

---

## Step 6: Add Global Custom CSS (15 minutes) **[BONUS]**

This step enhances the **primary column** (login form) to match your Hub UI.

### 6.1 Navigate to Custom CSS

1. Scroll down to the **Custom CSS** section in the branding editor
2. This is a separate section from the split layout custom code

### 6.2 Paste Global CSS

Copy and paste this entire CSS block:

```css
/* Global Custom CSS - applies to ALL AuthKit pages */

/* Enhance primary column background */
.ak-Background {
  background: light-dark(
    linear-gradient(135deg, #fafafa 0%, #ffffff 100%),
    linear-gradient(135deg, #0f172a 0%, #1e293b 100%)
  );
}

/* Style the main card with glass morphism */
.ak-Card {
  background: light-dark(
    rgba(255, 255, 255, 0.95),
    rgba(15, 23, 42, 0.95)
  ) !important;
  backdrop-filter: blur(10px);
  border: 1px solid light-dark(
    rgba(139, 92, 246, 0.1),
    rgba(167, 139, 250, 0.2)
  );
  box-shadow: 0 8px 32px light-dark(
    rgba(139, 92, 246, 0.1),
    rgba(0, 0, 0, 0.3)
  );
}

/* Enhance button hover states */
.ak-PrimaryButton {
  transition: all 0.3s ease;
}

.ak-PrimaryButton:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px light-dark(
    rgba(139, 92, 246, 0.3),
    rgba(167, 139, 250, 0.3)
  );
}

/* Add subtle animation to input fields */
.ak-Input:focus {
  border-color: light-dark(#8b5cf6, #a78bfa);
  box-shadow: 0 0 0 3px light-dark(
    rgba(139, 92, 246, 0.1),
    rgba(167, 139, 250, 0.2)
  );
  transition: all 0.2s ease;
}

/* Style the header with matching gradient */
.ak-Header .ak-Heading {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* Enhance social auth buttons */
.ak-AuthButton {
  transition: all 0.2s ease;
  border-color: light-dark(
    rgba(139, 92, 246, 0.2),
    rgba(167, 139, 250, 0.2)
  ) !important;
}

.ak-AuthButton:hover {
  transform: translateY(-1px);
  border-color: light-dark(
    rgba(139, 92, 246, 0.4),
    rgba(167, 139, 250, 0.4)
  ) !important;
  box-shadow: 0 2px 8px light-dark(
    rgba(139, 92, 246, 0.15),
    rgba(0, 0, 0, 0.2)
  );
}

/* Add subtle floating animation to the logo */
.ak-Logo {
  animation: float-subtle 6s ease-in-out infinite;
}

@keyframes float-subtle {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}
```

### 6.3 Preview Global Changes

The primary column should now have:
- ✅ Gradient text on the heading
- ✅ Glass morphism card effect
- ✅ Smooth button hover animations
- ✅ Purple focus states on inputs
- ✅ Subtle logo floating animation

---

## Step 7: Save and Test (13 minutes)

### 7.1 Save All Changes

Click **Save** or **Publish** in the WorkOS Dashboard.

### 7.2 Test Light Mode

1. Navigate to: `https://tools.genieos.namastex.io/login`
2. Click "Sign In with WorkOS"
3. **Verify**:
   - ✅ Custom logo appears
   - ✅ Purple button (#8b5cf6)
   - ✅ White background
   - ✅ Purple gradient heading
   - ✅ Animated gradient panel on right
   - ✅ Floating orbs visible
   - ✅ Feature cards with hover effects

### 7.3 Test Dark Mode

1. Switch your OS to dark mode
2. Refresh the login page
3. **Verify**:
   - ✅ Dark background (#0f172a)
   - ✅ Light purple button (#a78bfa)
   - ✅ Light purple links (#c4b5fd)
   - ✅ Dark gradient panel (deep purple)
   - ✅ All animations still working

### 7.4 Test Mobile

1. Resize browser to 375px width (or use mobile device)
2. **Verify**:
   - ✅ Layout is responsive
   - ✅ Secondary panel adapts properly
   - ✅ Text remains readable
   - ✅ Buttons are easy to tap

### 7.5 Test Complete Login Flow

1. Enter email on login page
2. **Expected**: No reload loop (PHASE 1 fix)
3. Complete authentication
4. **Expected**: Successfully log in and redirect to dashboard
5. Navigate to `/api/auth/user` with token
6. **Expected**: Returns user data (PHASE 2 fix)

### 7.6 Cross-Browser Testing

Test in:
- ✅ Chrome
- ✅ Firefox
- ✅ Safari
- ✅ Edge

### 7.7 Accessibility Check

1. Use browser dev tools (Lighthouse or axe DevTools)
2. **Check**:
   - ✅ Color contrast meets WCAG AA (4.5:1 minimum)
   - ✅ Buttons are keyboard accessible
   - ✅ Focus states are visible

---

## Troubleshooting

### Issue: Custom panel not showing

**Solution**: Ensure split layout is enabled and secondary panel position is set to "Right"

### Issue: Animations not working

**Solution**: Check that CSS was pasted in the CSS editor (not HTML editor)

### Issue: Colors don't match

**Solution**: Verify exact hex codes:
- Light purple: `#8b5cf6`
- Dark purple: `#a78bfa`
- Deep navy: `#0f172a`

### Issue: Mobile layout broken

**Solution**: Clear browser cache and test in incognito mode

### Issue: Login still has redirect loop

**Solution**: This was fixed in PHASE 1. Verify server was restarted with latest code.

---

## Maintenance

### Updating Branding

To modify branding in the future:

1. **Colors**: WorkOS Dashboard → Branding → Color
2. **Assets**: WorkOS Dashboard → Branding → Assets
3. **Custom Panel**: WorkOS Dashboard → Branding → Page Layout → Click secondary column
4. **Global CSS**: WorkOS Dashboard → Branding → Custom CSS

### Updating Copy

To translate or modify text:

1. Click on text in the AuthKit preview
2. Edit directly
3. WorkOS will auto-translate to all supported languages

---

## Color Reference

For future reference, here are all colors used:

### Primary Palette (Purple)
- `#8b5cf6` - Purple 500 (light mode primary)
- `#a78bfa` - Purple 400 (dark mode primary)
- `#c4b5fd` - Purple 300 (dark mode links)
- `#667eea` - Purple gradient start
- `#764ba2` - Purple gradient end

### Dark Mode Palette
- `#0f172a` - Slate 900 (dark background)
- `#1e293b` - Slate 800 (dark card)
- `#4c1d95` - Deep purple (dark gradient start)
- `#312e81` - Deep purple (dark gradient end)

### Light Mode Palette
- `#ffffff` - White (light background)
- `#fafafa` - Off-white (light gradient)

### Accent Colors
- `#3b82f6` - Blue 500 (floating orb)

---

## Success Checklist

After completing all steps, verify:

- [ ] Logo, icon, and favicon uploaded
- [ ] Colors configured (light and dark modes)
- [ ] Page settings configured (privacy, terms, names)
- [ ] Split layout enabled with secondary panel
- [ ] Custom HTML pasted (hero, features, footer)
- [ ] Custom CSS pasted (animations, gradients, orbs)
- [ ] Global custom CSS pasted (primary column styling)
- [ ] Saved all changes
- [ ] Tested light mode
- [ ] Tested dark mode
- [ ] Tested mobile responsiveness
- [ ] Tested complete login flow
- [ ] Cross-browser tested
- [ ] Accessibility verified

---

## Next Steps

Once branding is complete:

1. ✅ PHASE 1 COMPLETE: Redirect loop fixed
2. ✅ PHASE 2 COMPLETE: Architecture cleaned
3. ✅ PHASE 3 COMPLETE: Branding applied
4. 🎉 Enjoy your beautiful, branded WorkOS AuthKit login!

---

## Support

If you encounter issues:

- **WorkOS Docs**: https://workos.com/docs/authkit/branding
- **WorkOS Support**: support@workos.com
- **This Guide**: `/home/produser/prod/automagik-tools/docs/WORKOS_BRANDING_GUIDE.md`

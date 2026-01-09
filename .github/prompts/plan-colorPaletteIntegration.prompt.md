# Plan: Integrate Color Palette into LottoNz Website

Systematically apply the defined color scheme (primary dark-amethyst, accent princeton-orange, secondary banana-cream, tertiary blue-bell) throughout the frontend by updating Tailwind configuration and component styling.

## Steps

### 1. Update `tailwind.config.js`

Replace `nz-green` and `nz-blue` with semantic color scales using single color values with opacity modifiers.

**Color hierarchy:**
- **Base**: dark-amethyst (#3c2d66 / hsl(256, 39%, 29%)) - Main brand color for primary UI elements
- **Accent**: princeton-orange (#fe8302 / hsl(31, 99%, 50%)) - Powerball and call-to-action emphasis
- **Highlight-blue**: blue-bell (#0190d6 / hsl(200, 99%, 42%)) - Supporting color for accents and gradients
- **Highlight-cream**: banana-cream (#fef68a / hsl(56, 98%, 77%)) - Subtle highlights, badges, info panels

**Implementation approach:** Use single color values with Tailwind's opacity modifiers (e.g., `bg-base/50`, `text-accent/80`) instead of generating full 50-900 shade palettes

### 2. Modify `index.css`

Replace the body background gradient with dark-amethyst to blue-bell gradient.

**Current gradient:**
```css
background: linear-gradient(135deg, #1e3a8a 0%, #15803d 100%);
```

**New gradient:**
```css
background: linear-gradient(135deg, #3c2d66 0%, #0190d6 100%);
```

**Note:** Do NOT define CSS custom properties - Tailwind will be the single source of truth for colors

### 3. Refactor `App.tsx`

Systematically replace all color classes throughout the component:

**Color class replacements:**
- `nz-green-*` → `base` with opacity modifiers (e.g., `bg-base`, `bg-base/10`, `text-base/70`)
- `nz-blue-*` → `highlight-blue` with opacity modifiers
- `red-*` (powerball) → `accent` with opacity modifiers
- Apply `highlight-cream` for subtle highlights, badges, or information panels

**Specific component updates:**

**Background:**
- Body gradient: Already updated in `index.css` to use dark-amethyst → blue-bell

**Latest Result Card:**
- Lottery balls: `from-nz-green-400 to-nz-green-600` → `from-base to-base` (use same base color with gradient)
- Powerball: `from-red-400 to-red-600` → `from-accent to-accent` (use same accent color with gradient)
- Icons: `text-nz-green-300`, `text-nz-blue-300` → `text-base/60`, `text-highlight-blue/60`
- Subtitle: `text-nz-blue-100` → `text-highlight-blue/30`
- Date: `text-nz-blue-200` → `text-highlight-blue/40`

**Main Card:**
- Settings icon: `text-nz-blue-600` → `text-highlight-blue`

**Preference Buttons:**
- Active state: `bg-nz-green-600` → `bg-base` or `bg-nz-blue-600` → `bg-highlight-blue`

**Generated Numbers:**
- Container background: `from-nz-green-50 to-nz-blue-50` → `from-base/10 to-highlight-blue/10`
- Border: `border-nz-green-200` → `border-base/20`
- Lottery balls: `from-nz-green-500 to-nz-green-700` → `from-base to-base` (darken with shadow instead)
- Powerball: `from-red-500 to-red-700` → `from-accent to-accent`

**Generate Button:**
- Gradient: `from-nz-green-600 to-nz-blue-600` → `from-base to-highlight-blue`
- Hover: `from-nz-green-700 to-nz-blue-700` → `from-base/90 to-highlight-blue/90`

**Optional - Add highlight-cream usage:**
- Consider adding `highlight-cream` for info badges, tooltips, or subtle number highlights

### 4. Test color contrast and accessibility

Verify text readbase (dark-amethyst) - should pass AAA
- White text on accent (princeton-orange) - verify AA minimum
- Dark text on highlight-cream (banana-cream) - should pass AAA
- White text on highlight-blue (blue-bell) - verify AA minimumst)
- White text on accent (princeton-orange)
- Dark text on secondary (banana-cream)
- White text on tertiary (blue-bell)

## Implementation Decisions

### ✅ 1. Shade generation approach

**Decision:** Use opacity modifiers (Option C)

Single color values with Tailwind's built-in opacity utilities (e.g., `/10`, `/20`, `/50`, `/80`) for variations instead of generating full shade palettes.

### ✅ 2. Handle `color-palette.css`

**Decision:** Deprecate - Tailwind is source of truth

The `color-palette.css` file will be kept as a reference but not imported or used. All color definitions will be managed in `tailwind.config.js`.

### ✅ 3. Color usage strategy

**Base (dark-amethyst):**
- Primary brand color
- Main lottery number balls
- Active states
- Primary buttons and CTAs

**Accent (princeton-orange):**
- Powerball emphasis
- Important CTAs
- Attention-grabbing elements

**Highlight-blue (blue-bell):**
- Supporting gradients
- Secondary actions
- Text accents
- Alternative active states

**Highlight-cream (banana-cream):**
- Info badges
- Tooltips
- Subtle background highlights
- Number metadata or labels

### 4. Additional utility colors from palette

AvaUpdate Tailwind config with new base color definitions
2. Update index.css background gradient
3. Refactor App.tsx to replace all color classes with new system
4. Test in browser for visual consistency
5. Check accessibility/contrast ratios
6. Add deprecation comment to color-palette.css

## Files to Update

- `Frontend/tailwind.config.js` - Add base, accent, highlight-blue, highlight-cream colors
- `Frontend/src/index.css` - Update body gradient to dark-amethyst → blue-bell
- `Frontend/src/App.tsx` - Replace all nz-green-*, nz-blue-*, red-* classes
- `Frontend/src/color-palette.css` - Add deprecation notice comment at top
4. ✅ Test in browser for visual consistency
5. ✅ Check accessibility/contrast
6. ✅ Refine shades if needed

## Files to Update

- `Frontend/tailwind.config.js`
- `Frontend/src/index.css`
- `Frontend/src/App.tsx`
- `Frontend/src/color-palette.css` (optional - convert or deprecate)

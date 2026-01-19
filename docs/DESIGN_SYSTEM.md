# Design System (SOD)
## KnowledgeTree Platform

**Version**: 1.0
**Date**: January 19, 2026
**Status**: Design Specification

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Iconography](#iconography)
5. [Spacing & Layout](#spacing--layout)
6. [Components](#components)
7. [Animations & Transitions](#animations--transitions)
8. [Dark Mode](#dark-mode)
9. [Internationalization](#internationalization)
10. [Accessibility](#accessibility)
11. [Implementation Guide](#implementation-guide)

---

## Design Philosophy

### Core Principles

**Professional & Focused**
- Clean, business-oriented interface without decorative elements
- No emojis or playful graphics - pure functionality
- Information-dense but not cluttered
- Prioritize readability and scannability

**Modern & Timeless**
- Inspired by Notion's clean aesthetic
- Pastel color palette for reduced eye strain
- Soft shadows and subtle blur effects
- Smooth, purposeful animations

**Accessible & Inclusive**
- WCAG 2.1 AA compliance minimum
- High contrast ratios (4.5:1 for text, 3:1 for UI)
- Keyboard navigation for all features
- Screen reader friendly

**Consistent & Predictable**
- Single source of truth for design tokens
- Reusable component patterns
- Uniform spacing and sizing system
- Coherent interaction patterns

### Design Inspiration

**Primary References**:
- **Notion**: Typography, spacing, hierarchy, clean layouts
- **Linear**: Animations, command palette, keyboard shortcuts
- **Raycast**: Fast, fluid interactions, blurred backgrounds
- **Arc Browser**: Pastel colors, modern aesthetics

**Anti-patterns** (Avoid):
- Overly colorful "startup" aesthetics
- Gratuitous animations or transitions
- Emoji-heavy interfaces
- Cluttered information architecture

---

## Color System

### Base Palette (Pastel Theme)

**Neutrals** (Grayscale)
```css
--color-neutral-50:  #FAFAFA  /* Lightest background */
--color-neutral-100: #F5F5F5  /* Subtle background */
--color-neutral-200: #E5E5E5  /* Borders, dividers */
--color-neutral-300: #D4D4D4  /* Disabled state */
--color-neutral-400: #A3A3A3  /* Placeholder text */
--color-neutral-500: #737373  /* Secondary text */
--color-neutral-600: #525252  /* Body text */
--color-neutral-700: #404040  /* Headings */
--color-neutral-800: #262626  /* High emphasis */
--color-neutral-900: #171717  /* Maximum contrast */
```

**Primary (Pastel Blue)** - Main actions, links, focus states
```css
--color-primary-50:  #EFF6FF  /* Lightest tint */
--color-primary-100: #DBEAFE  /* Hover backgrounds */
--color-primary-200: #BFDBFE  /* Selected states */
--color-primary-300: #93C5FD  /* Borders */
--color-primary-400: #60A5FA  /* Icons, accents */
--color-primary-500: #3B82F6  /* Default primary */
--color-primary-600: #2563EB  /* Hover state */
--color-primary-700: #1D4ED8  /* Active state */
--color-primary-800: #1E40AF  /* Dark mode primary */
--color-primary-900: #1E3A8A  /* Maximum contrast */
```

**Success (Pastel Green)** - Positive feedback, success states
```css
--color-success-50:  #F0FDF4
--color-success-100: #DCFCE7
--color-success-200: #BBF7D0
--color-success-300: #86EFAC
--color-success-400: #4ADE80
--color-success-500: #22C55E  /* Default success */
--color-success-600: #16A34A
--color-success-700: #15803D
--color-success-800: #166534
--color-success-900: #14532D
```

**Warning (Pastel Yellow/Amber)** - Warnings, pending states
```css
--color-warning-50:  #FFFBEB
--color-warning-100: #FEF3C7
--color-warning-200: #FDE68A
--color-warning-300: #FCD34D
--color-warning-400: #FBBF24
--color-warning-500: #F59E0B  /* Default warning */
--color-warning-600: #D97706
--color-warning-700: #B45309
--color-warning-800: #92400E
--color-warning-900: #78350F
```

**Error (Pastel Red)** - Errors, destructive actions
```css
--color-error-50:  #FEF2F2
--color-error-100: #FEE2E2
--color-error-200: #FECACA
--color-error-300: #FCA5A5
--color-error-400: #F87171
--color-error-500: #EF4444  /* Default error */
--color-error-600: #DC2626
--color-error-700: #B91C1C
--color-error-800: #991B1B
--color-error-900: #7F1D1D
```

**Info (Pastel Teal)** - Informational messages, tooltips
```css
--color-info-50:  #F0FDFA
--color-info-100: #CCFBF1
--color-info-200: #99F6E4
--color-info-300: #5EEAD4
--color-info-400: #2DD4BF
--color-info-500: #14B8A6  /* Default info */
--color-info-600: #0D9488
--color-info-700: #0F766E
--color-info-800: #115E59
--color-info-900: #134E4A
```

### Semantic Colors

**Backgrounds**
```css
--bg-primary: var(--color-neutral-50)      /* Main background */
--bg-secondary: #FFFFFF                     /* Card, panel backgrounds */
--bg-tertiary: var(--color-neutral-100)    /* Subtle raised elements */
--bg-hover: var(--color-primary-50)        /* Hover states */
--bg-selected: var(--color-primary-100)    /* Selected items */
--bg-disabled: var(--color-neutral-200)    /* Disabled elements */
```

**Text Colors**
```css
--text-primary: var(--color-neutral-800)     /* Headings, body text */
--text-secondary: var(--color-neutral-600)   /* Secondary information */
--text-tertiary: var(--color-neutral-500)    /* Tertiary, metadata */
--text-placeholder: var(--color-neutral-400) /* Placeholder text */
--text-disabled: var(--color-neutral-300)    /* Disabled text */
--text-link: var(--color-primary-600)        /* Links */
--text-inverse: #FFFFFF                       /* Text on dark backgrounds */
```

**Borders**
```css
--border-default: var(--color-neutral-200)   /* Default borders */
--border-strong: var(--color-neutral-300)    /* Emphasized borders */
--border-focus: var(--color-primary-500)     /* Focus rings */
--border-error: var(--color-error-500)       /* Error states */
```

### Category Colors (Pastel Palette)

For highlighting categories in tree view:
```css
--category-lavender: #E6E6FA  /* Soft purple */
--category-mint:     #E0F8F1  /* Soft mint green */
--category-peach:    #FFE5D9  /* Soft peach */
--category-sky:      #E0F4FF  /* Soft sky blue */
--category-rose:     #FFE5E5  /* Soft rose */
--category-lemon:    #FFFACD  /* Soft lemon */
--category-sage:     #E8F5E9  /* Soft sage green */
--category-lilac:    #F3E5F5  /* Soft lilac */
```

### Usage Guidelines

**Do's**:
- Use primary blue for primary actions (Save, Create, Submit)
- Use success green for completed states, confirmations
- Use warning amber for non-critical alerts, pending states
- Use error red sparingly, only for destructive actions or errors
- Maintain 4.5:1 contrast ratio for text

**Don'ts**:
- Don't use more than 3 colors in a single component
- Don't use pure black (#000000) or pure white (#FFFFFF) for text
- Don't use saturated colors (use pastels)
- Don't rely on color alone to convey information

---

## Typography

### Font Family

**Primary Font**: **Inter** (same as Notion)
- **Why**: Optimized for UI, excellent readability, variable font support
- **Weights**: 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)
- **Source**: Google Fonts or self-hosted

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

--font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', 'Droid Sans Mono', 'Source Code Pro', monospace;
```

### Type Scale

**Display (Headings)**
```css
--text-display-2xl: 4.5rem   /* 72px - Hero */
--text-display-xl:  3.75rem  /* 60px - Page title */
--text-display-lg:  3rem     /* 48px - Section title */
--text-display-md:  2.25rem  /* 36px - Card title */
--text-display-sm:  1.875rem /* 30px - Subsection */
```

**Text (Body)**
```css
--text-xl:  1.25rem   /* 20px - Large body */
--text-lg:  1.125rem  /* 18px - Default body */
--text-base: 1rem     /* 16px - Small body */
--text-sm:  0.875rem  /* 14px - Caption, metadata */
--text-xs:  0.75rem   /* 12px - Tiny labels */
```

**Line Heights**
```css
--line-height-tight:  1.25   /* Headings */
--line-height-normal: 1.5    /* Body text */
--line-height-relaxed: 1.75  /* Long-form content */
```

**Font Weights**
```css
--font-weight-regular:  400  /* Body text */
--font-weight-medium:   500  /* Emphasized text */
--font-weight-semibold: 600  /* Subheadings */
--font-weight-bold:     700  /* Headings */
```

### Typography Hierarchy

**Page Title**
```css
font-size: var(--text-display-lg);    /* 48px */
font-weight: var(--font-weight-bold);  /* 700 */
line-height: var(--line-height-tight); /* 1.25 */
color: var(--text-primary);
letter-spacing: -0.02em;
```

**Section Heading**
```css
font-size: var(--text-display-md);       /* 36px */
font-weight: var(--font-weight-semibold); /* 600 */
line-height: var(--line-height-tight);    /* 1.25 */
color: var(--text-primary);
```

**Card/Component Title**
```css
font-size: var(--text-xl);                 /* 20px */
font-weight: var(--font-weight-semibold);  /* 600 */
line-height: var(--line-height-normal);    /* 1.5 */
color: var(--text-primary);
```

**Body Text (Default)**
```css
font-size: var(--text-lg);               /* 18px */
font-weight: var(--font-weight-regular); /* 400 */
line-height: var(--line-height-normal);  /* 1.5 */
color: var(--text-primary);
```

**Caption/Metadata**
```css
font-size: var(--text-sm);               /* 14px */
font-weight: var(--font-weight-regular); /* 400 */
line-height: var(--line-height-normal);  /* 1.5 */
color: var(--text-secondary);
```

### Polish Language Considerations

**Diacritics Support**: Inter font fully supports Polish characters (ą, ć, ę, ł, ń, ó, ś, ź, ż)

**Longer Text**: Polish text is typically 20-30% longer than English
- Allow flexible layouts
- Test with Polish strings
- Use truncation with ellipsis for overflows

**Example Translations**:
```typescript
// English: "Create new project" (18 chars)
// Polish: "Utwórz nowy projekt" (19 chars)

// English: "Search documents" (16 chars)
// Polish: "Wyszukaj dokumenty" (18 chars)
```

---

## Iconography

### Icon Library: Lucide React

**Why Lucide**:
- 1000+ professionally designed SVG icons
- Consistent 24x24px grid
- Lightweight (tree-shakable)
- Open source (MIT license)
- Perfect for business/productivity apps

**Installation**:
```bash
npm install lucide-react
```

**Usage**:
```tsx
import { Search, FileText, Settings, ChevronDown } from 'lucide-react';

<Search className="w-5 h-5 text-neutral-600" />
```

### Icon Sizes

```css
--icon-xs:  12px  /* Inline with text-xs */
--icon-sm:  16px  /* Inline with text-sm */
--icon-md:  20px  /* Default, inline with text-base */
--icon-lg:  24px  /* Standalone icons */
--icon-xl:  32px  /* Large feature icons */
--icon-2xl: 48px  /* Hero icons */
```

### Icon Usage Guidelines

**Do's**:
- Use consistent stroke width (2px default)
- Maintain 1:1 aspect ratio
- Use semantic color matching context
- Provide accessible labels (aria-label)

**Don'ts**:
- Don't mix icon styles (outline with filled)
- Don't use decorative icons without purpose
- Don't scale icons non-uniformly
- Don't use emojis as icons

### Key Icons Mapping

**Navigation & Structure**:
```typescript
Home, Folder, FileText, Search, Settings, Menu, ChevronRight,
ChevronDown, ArrowLeft, ArrowRight, MoreHorizontal
```

**Actions**:
```typescript
Plus, Trash2, Edit3, Copy, Download, Upload, RefreshCw,
Check, X, Save, Send, ExternalLink
```

**Document Operations**:
```typescript
FileText, FilePlus, FileSearch, FileDown, FileUp,
FileCode, FileCog, FileWarning
```

**RAG & Knowledge**:
```typescript
Brain, BookOpen, MessageSquare, Sparkles, Zap,
Database, Layers, Network
```

**Status & Feedback**:
```typescript
CheckCircle2, AlertCircle, AlertTriangle, Info,
Loader2 (animated), Clock, TrendingUp, TrendingDown
```

**User & Account**:
```typescript
User, Users, UserPlus, LogIn, LogOut, Key, Shield,
CreditCard, Crown (premium)
```

### Custom Icons (SVG)

For brand-specific icons not in Lucide:
```tsx
// components/icons/KnowledgeTreeLogo.tsx
export const KnowledgeTreeLogo = ({ className }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    {/* Custom SVG paths */}
  </svg>
);
```

**Guidelines for Custom Icons**:
- 24x24px viewBox
- 2px stroke width
- currentColor for fills/strokes (inherit from text color)
- Optimize with SVGO

---

## Spacing & Layout

### Spacing Scale (8px Base)

```css
--space-0:   0px     /* No spacing */
--space-1:   4px     /* 0.25rem - Tight spacing */
--space-2:   8px     /* 0.5rem - Base unit */
--space-3:   12px    /* 0.75rem - Small gap */
--space-4:   16px    /* 1rem - Default gap */
--space-5:   20px    /* 1.25rem - Medium gap */
--space-6:   24px    /* 1.5rem - Large gap */
--space-8:   32px    /* 2rem - Section gap */
--space-10:  40px    /* 2.5rem - Large section */
--space-12:  48px    /* 3rem - XL section */
--space-16:  64px    /* 4rem - Page margins */
--space-20:  80px    /* 5rem - Hero spacing */
--space-24:  96px    /* 6rem - Maximum spacing */
```

### Layout Containers

**Max Widths**:
```css
--max-width-xs:   20rem   /* 320px - Narrow forms */
--max-width-sm:   24rem   /* 384px - Small cards */
--max-width-md:   28rem   /* 448px - Standard modals */
--max-width-lg:   32rem   /* 512px - Wide modals */
--max-width-xl:   36rem   /* 576px - Large forms */
--max-width-2xl:  42rem   /* 672px - Prose content */
--max-width-3xl:  48rem   /* 768px - Wide content */
--max-width-4xl:  56rem   /* 896px - Dashboard panels */
--max-width-5xl:  64rem   /* 1024px - Main content area */
--max-width-6xl:  72rem   /* 1152px - Wide dashboard */
--max-width-7xl:  80rem   /* 1280px - Full width app */
```

**Grid System** (12-column):
```css
display: grid;
grid-template-columns: repeat(12, minmax(0, 1fr));
gap: var(--space-4); /* 16px */
```

**Common Layouts**:

1. **Sidebar Layout** (Category Tree + Main Content):
```css
.layout-sidebar {
  display: grid;
  grid-template-columns: 280px 1fr; /* Fixed sidebar, flexible content */
  gap: 0;
  height: 100vh;
}
```

2. **Three-Column Layout** (Sidebar + Main + Details):
```css
.layout-three-column {
  display: grid;
  grid-template-columns: 280px 1fr 400px;
  gap: 0;
  height: 100vh;
}
```

3. **Dashboard Grid**:
```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-6);
}
```

### Border Radius

```css
--radius-none: 0px      /* Sharp corners */
--radius-sm:   4px      /* Subtle rounding */
--radius-md:   6px      /* Default radius */
--radius-lg:   8px      /* Cards, buttons */
--radius-xl:   12px     /* Panels, modals */
--radius-2xl:  16px     /* Large cards */
--radius-3xl:  24px     /* Hero elements */
--radius-full: 9999px   /* Pills, avatars */
```

**Usage**:
- Buttons: `--radius-lg` (8px)
- Inputs: `--radius-md` (6px)
- Cards: `--radius-xl` (12px)
- Modals: `--radius-2xl` (16px)
- Avatars: `--radius-full`

### Shadows & Elevation

**Elevation Levels**:
```css
/* Level 0 - Flat (no shadow) */
--shadow-none: none;

/* Level 1 - Subtle lift (cards on background) */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

/* Level 2 - Default (buttons, inputs) */
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
             0 2px 4px -1px rgba(0, 0, 0, 0.06);

/* Level 3 - Raised (dropdowns, popovers) */
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
             0 4px 6px -2px rgba(0, 0, 0, 0.05);

/* Level 4 - Floating (modals, dialogs) */
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
             0 10px 10px -5px rgba(0, 0, 0, 0.04);

/* Level 5 - Maximum (tooltips, notifications) */
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

**Inner Shadows** (for inputs):
```css
--shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
```

### Blur Effects (Modern Glassmorphism)

```css
--blur-sm:  4px   /* Subtle blur */
--blur-md:  8px   /* Default blur */
--blur-lg:  12px  /* Strong blur */
--blur-xl:  16px  /* Maximum blur */
```

**Usage Example** (Blurred Panel):
```css
.panel-blur {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(var(--blur-md));
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

---

## Components

### Button Variants

**Primary Button** (Main actions):
```tsx
<Button variant="primary" size="md">
  Utwórz projekt
</Button>
```
```css
.button-primary {
  background: var(--color-primary-500);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-medium);
  transition: all 150ms ease;
}

.button-primary:hover {
  background: var(--color-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.button-primary:active {
  transform: translateY(0);
  box-shadow: var(--shadow-sm);
}
```

**Secondary Button** (Alternative actions):
```css
.button-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.button-secondary:hover {
  background: var(--bg-hover);
  border-color: var(--color-primary-300);
}
```

**Ghost Button** (Tertiary actions):
```css
.button-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: none;
}

.button-ghost:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
```

**Destructive Button** (Delete, remove):
```css
.button-destructive {
  background: var(--color-error-500);
  color: white;
  border: none;
}

.button-destructive:hover {
  background: var(--color-error-600);
}
```

**Button Sizes**:
```css
.button-sm {
  padding: 6px 12px;
  font-size: var(--text-sm);
  height: 32px;
}

.button-md {
  padding: 10px 16px;
  font-size: var(--text-base);
  height: 40px;
}

.button-lg {
  padding: 12px 20px;
  font-size: var(--text-lg);
  height: 48px;
}
```

### Input Fields

**Text Input**:
```tsx
<Input
  type="text"
  placeholder="Nazwa projektu..."
  value={value}
  onChange={onChange}
/>
```
```css
.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: white;
  color: var(--text-primary);
  font-size: var(--text-base);
  transition: all 150ms ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.input:disabled {
  background: var(--bg-disabled);
  color: var(--text-disabled);
  cursor: not-allowed;
}

.input::placeholder {
  color: var(--text-placeholder);
}
```

**Input with Icon**:
```tsx
<div className="input-with-icon">
  <Search className="input-icon" />
  <input type="text" placeholder="Wyszukaj..." />
</div>
```
```css
.input-with-icon {
  position: relative;
}

.input-with-icon input {
  padding-left: 36px;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  pointer-events: none;
}
```

### Cards

**Basic Card**:
```tsx
<Card>
  <CardHeader>
    <CardTitle>Tytuł karty</CardTitle>
    <CardDescription>Opis karty</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```
```css
.card {
  background: white;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all 200ms ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-header {
  padding: var(--space-6);
  border-bottom: 1px solid var(--border-default);
}

.card-content {
  padding: var(--space-6);
}
```

### Modals & Dialogs

**Modal Overlay**:
```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(var(--blur-sm));
  z-index: 50;
  animation: fadeIn 150ms ease;
}

.modal-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-2xl);
  max-width: var(--max-width-lg);
  width: 90vw;
  max-height: 85vh;
  overflow: auto;
  animation: scaleIn 200ms ease;
}
```

### Tree View (Category Editor)

**Tree Node**:
```tsx
<TreeNode
  label="Kategoria"
  icon={<Folder />}
  expanded={true}
  selected={false}
  depth={0}
>
  {/* Children */}
</TreeNode>
```
```css
.tree-node {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  padding-left: calc(var(--depth) * 20px + 8px);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 100ms ease;
}

.tree-node:hover {
  background: var(--bg-hover);
}

.tree-node.selected {
  background: var(--bg-selected);
  color: var(--color-primary-700);
  font-weight: var(--font-weight-medium);
}

.tree-node-icon {
  margin-right: var(--space-2);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.tree-node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

### Toast Notifications

**Toast Container**:
```css
.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: white;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  min-width: 300px;
  max-width: 400px;
  animation: slideInRight 200ms ease;
}

.toast-success {
  border-left: 4px solid var(--color-success-500);
}

.toast-error {
  border-left: 4px solid var(--color-error-500);
}

.toast-warning {
  border-left: 4px solid var(--color-warning-500);
}

.toast-info {
  border-left: 4px solid var(--color-info-500);
}
```

---

## Animations & Transitions

### Motion Principles

**Purposeful**: Every animation should serve a function
- Provide feedback (button press)
- Show relationships (expand/collapse)
- Direct attention (loading states)
- Enhance perceived performance

**Natural**: Use spring physics for organic feel
```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
>
  Content
</motion.div>
```

**Fast**: Keep animations short (100-300ms)
- Micro-interactions: 100-150ms
- Standard transitions: 150-200ms
- Complex animations: 200-300ms
- Never exceed 500ms

### Standard Transitions

**Fade In/Out**:
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 150ms ease;
}
```

**Slide In/Out**:
```css
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

**Scale In/Out**:
```css
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Loading States

**Spinner** (Animated icon):
```tsx
<Loader2 className="animate-spin" />
```
```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
```

**Skeleton Loader**:
```css
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-neutral-200) 0%,
    var(--color-neutral-300) 50%,
    var(--color-neutral-200) 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
  border-radius: var(--radius-md);
}
```

**Progress Bar**:
```tsx
<ProgressBar value={45} max={100} />
```
```css
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--color-neutral-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary-500);
  transition: width 300ms ease;
  border-radius: var(--radius-full);
}
```

### Hover Effects

**Button Lift**:
```css
.button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.button:active {
  transform: translateY(0);
}
```

**Card Lift**:
```css
.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

### Page Transitions

**Route Change** (Framer Motion):
```tsx
<motion.div
  key={location.pathname}
  initial={{ opacity: 0, x: -20 }}
  animate={{ opacity: 1, x: 0 }}
  exit={{ opacity: 0, x: 20 }}
  transition={{ duration: 0.2 }}
>
  {children}
</motion.div>
```

---

## Dark Mode

### Dark Mode Colors

**Neutrals (Dark)**:
```css
--color-neutral-dark-50:  #18181B  /* Darkest background */
--color-neutral-dark-100: #27272A  /* Subtle background */
--color-neutral-dark-200: #3F3F46  /* Borders, dividers */
--color-neutral-dark-300: #52525B  /* Disabled state */
--color-neutral-dark-400: #71717A  /* Placeholder text */
--color-neutral-dark-500: #A1A1AA  /* Secondary text */
--color-neutral-dark-600: #D4D4D8  /* Body text */
--color-neutral-dark-700: #E4E4E7  /* Headings */
--color-neutral-dark-800: #F4F4F5  /* High emphasis */
--color-neutral-dark-900: #FAFAFA  /* Maximum contrast */
```

**Semantic Colors (Dark Mode)**:
```css
[data-theme='dark'] {
  /* Backgrounds */
  --bg-primary: var(--color-neutral-dark-50);
  --bg-secondary: var(--color-neutral-dark-100);
  --bg-tertiary: var(--color-neutral-dark-200);
  --bg-hover: rgba(59, 130, 246, 0.1);    /* Primary-50 with opacity */
  --bg-selected: rgba(59, 130, 246, 0.2);  /* Primary-100 with opacity */

  /* Text */
  --text-primary: var(--color-neutral-dark-700);
  --text-secondary: var(--color-neutral-dark-500);
  --text-tertiary: var(--color-neutral-dark-400);
  --text-placeholder: var(--color-neutral-dark-400);

  /* Borders */
  --border-default: var(--color-neutral-dark-200);
  --border-strong: var(--color-neutral-dark-300);

  /* Shadows (darker, more subtle) */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4),
               0 2px 4px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5),
               0 4px 6px -2px rgba(0, 0, 0, 0.4);
}
```

### Theme Switcher Implementation

**React Context**:
```tsx
// context/ThemeContext.tsx
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (theme: Theme) => void;
}>({
  theme: 'system',
  setTheme: () => {},
});

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme;
    if (stored) setTheme(stored);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';

    const appliedTheme = theme === 'system' ? systemTheme : theme;
    root.setAttribute('data-theme', appliedTheme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
```

**Theme Toggle Component**:
```tsx
// components/ThemeToggle.tsx
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

export const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex gap-1 p-1 bg-neutral-100 dark:bg-neutral-dark-200 rounded-lg">
      <button
        onClick={() => setTheme('light')}
        className={theme === 'light' ? 'active' : ''}
      >
        <Sun className="w-4 h-4" />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={theme === 'dark' ? 'active' : ''}
      >
        <Moon className="w-4 h-4" />
      </button>
      <button
        onClick={() => setTheme('system')}
        className={theme === 'system' ? 'active' : ''}
      >
        <Monitor className="w-4 h-4" />
      </button>
    </div>
  );
};
```

---

## Internationalization

### Implementation (react-i18next)

**Setup**:
```bash
npm install react-i18next i18next i18next-browser-languagedetector
```

**Configuration** (`i18n.ts`):
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import plCommon from './locales/pl/common.json';
import plEditor from './locales/pl/editor.json';
import enCommon from './locales/en/common.json';
import enEditor from './locales/en/editor.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      pl: {
        common: plCommon,
        editor: plEditor,
      },
      en: {
        common: enCommon,
        editor: enEditor,
      },
    },
    fallbackLng: 'pl',  // Polish as default
    defaultNS: 'common',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
```

### Translation Files

**Polish** (`locales/pl/common.json`):
```json
{
  "app": {
    "name": "KnowledgeTree",
    "tagline": "Platforma zarządzania wiedzą"
  },
  "nav": {
    "projects": "Projekty",
    "search": "Wyszukaj",
    "settings": "Ustawienia"
  },
  "actions": {
    "create": "Utwórz",
    "edit": "Edytuj",
    "delete": "Usuń",
    "save": "Zapisz",
    "cancel": "Anuluj",
    "export": "Eksportuj",
    "import": "Importuj"
  },
  "project": {
    "create": "Utwórz projekt",
    "name": "Nazwa projektu",
    "description": "Opis projektu",
    "created": "Projekt utworzony",
    "deleted": "Projekt usunięty"
  }
}
```

**English** (`locales/en/common.json`):
```json
{
  "app": {
    "name": "KnowledgeTree",
    "tagline": "Knowledge Management Platform"
  },
  "nav": {
    "projects": "Projects",
    "search": "Search",
    "settings": "Settings"
  },
  "actions": {
    "create": "Create",
    "edit": "Edit",
    "delete": "Delete",
    "save": "Save",
    "cancel": "Cancel",
    "export": "Export",
    "import": "Import"
  },
  "project": {
    "create": "Create project",
    "name": "Project name",
    "description": "Project description",
    "created": "Project created",
    "deleted": "Project deleted"
  }
}
```

### Usage in Components

```tsx
import { useTranslation } from 'react-i18next';

export const ProjectCard = () => {
  const { t } = useTranslation('common');

  return (
    <div>
      <h2>{t('project.name')}</h2>
      <button>{t('actions.create')}</button>
    </div>
  );
};
```

### Language Switcher

```tsx
// components/LanguageSwitcher.tsx
import { useTranslation } from 'react-i18next';
import { Languages } from 'lucide-react';

export const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'pl' ? 'en' : 'pl';
    i18n.changeLanguage(newLang);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-100"
    >
      <Languages className="w-4 h-4" />
      <span className="text-sm font-medium">
        {i18n.language === 'pl' ? 'EN' : 'PL'}
      </span>
    </button>
  );
};
```

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast**:
- Text: 4.5:1 minimum (7:1 for AAA)
- UI elements: 3:1 minimum
- Large text (18pt+): 3:1 minimum

**Keyboard Navigation**:
- All interactive elements focusable
- Logical tab order
- Skip links for screen readers
- Visible focus indicators (focus rings)

**Screen Readers**:
- Semantic HTML (`<nav>`, `<main>`, `<aside>`)
- ARIA labels for icons and images
- ARIA live regions for dynamic content
- Descriptive link text (no "click here")

### Focus Styles

```css
/* Visible focus ring */
:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}

/* Remove default outline */
:focus:not(:focus-visible) {
  outline: none;
}

/* Button focus */
.button:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}
```

### ARIA Patterns

**Tree View**:
```tsx
<div role="tree" aria-label="Category tree">
  <div role="treeitem" aria-expanded="true" aria-level="1">
    Category Name
  </div>
</div>
```

**Modal**:
```tsx
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Modal Title</h2>
</div>
```

**Loading State**:
```tsx
<div role="status" aria-live="polite" aria-busy="true">
  Ładowanie...
</div>
```

---

## Implementation Guide

### Step 1: Setup TailwindCSS with Design Tokens

**tailwind.config.js**:
```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        neutral: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          // ... rest of neutral scale
        },
        primary: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          // ... rest of primary scale
        },
        // ... other semantic colors
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'monospace'],
      },
      spacing: {
        // Extend default spacing with custom values
      },
      borderRadius: {
        none: '0px',
        sm: '4px',
        md: '6px',
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
        '3xl': '24px',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        // ... rest of shadows
      },
    },
  },
  plugins: [],
};
```

### Step 2: Configure Fonts

**index.html** (Google Fonts):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**globals.css**:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 18px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Step 3: Install Dependencies

```bash
# Core UI
npm install lucide-react framer-motion

# Internationalization
npm install react-i18next i18next i18next-browser-languagedetector

# shadcn/ui (install CLI first)
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card dialog
```

### Step 4: Implement Theme Provider

Create `ThemeProvider` and `LanguageProvider` as shown in sections above.

### Step 5: Create Component Library

Build reusable components following patterns in this design system.

---

## Checklist

### Design Implementation Checklist

- [ ] TailwindCSS configured with design tokens
- [ ] Inter font loaded and applied
- [ ] Color palette implemented (light + dark)
- [ ] Spacing scale configured
- [ ] Typography hierarchy defined
- [ ] Lucide React icons integrated
- [ ] shadcn/ui components installed
- [ ] Framer Motion configured
- [ ] Dark mode toggle working
- [ ] i18n setup with Polish + English
- [ ] Focus styles implemented
- [ ] ARIA labels added to components
- [ ] Keyboard navigation tested
- [ ] Color contrast validated (WCAG AA)
- [ ] Responsive design tested (mobile, tablet, desktop)

---

## Resources

**Design Tools**:
- Figma: UI mockups and prototypes
- Coolors: Color palette generation
- Contrast Checker: WCAG compliance testing

**Icon Resources**:
- Lucide Icons: https://lucide.dev
- Heroicons: https://heroicons.com (alternative)

**Typography**:
- Inter Font: https://rsms.me/inter/
- Google Fonts: https://fonts.google.com

**Animation**:
- Framer Motion: https://www.framer.com/motion/
- Animation Examples: https://www.framer.com/motion/examples/

**Accessibility**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/

---

**Document Version**: 1.0
**Last Updated**: January 19, 2026
**Next Review**: After UI implementation Phase 1

---

*End of Design System Document*

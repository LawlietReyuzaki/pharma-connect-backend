# Red Dot Pharmacy - Design System & Style Guide

## Table of Contents
1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Buttons](#buttons)
4. [Cards & Containers](#cards--containers)
5. [Form Elements](#form-elements)
6. [Shadows & Elevation](#shadows--elevation)
7. [Animations & Transitions](#animations--transitions)
8. [Spacing System](#spacing-system)
9. [Border Radius](#border-radius)
10. [Icons](#icons)
11. [Responsive Breakpoints](#responsive-breakpoints)

---

## Color Palette

### Primary Colors
| Name | Hex Code | RGB | Usage |
|------|----------|-----|-------|
| Navy Blue (Primary) | `#1e3a5f` | rgb(30, 58, 95) | Headers, buttons, primary actions |
| Dark Navy | `#0f2744` | rgb(15, 39, 68) | Gradients, dark accents |
| Navy Light | `#2d4a6f` | rgb(45, 74, 111) | Hover states |

### Secondary Colors
| Name | Hex Code | RGB | Usage |
|------|----------|-----|-------|
| Royal Blue | `#2563eb` | rgb(37, 99, 235) | Active states, links |
| Indigo | `#4f46e5` | rgb(79, 70, 229) | User avatars, accents |
| Purple | `#6366f1` | rgb(99, 102, 241) | User message bubbles |

### Semantic Colors
| Name | Hex Code | RGB | Usage |
|------|----------|-----|-------|
| Success Green | `#22c55e` | rgb(34, 197, 94) | Success states, online status |
| Success Dark | `#16a34a` | rgb(22, 163, 74) | Success hover |
| Warning Orange | `#f59e0b` | rgb(245, 158, 11) | Warnings, cautions |
| Danger Red | `#dc2626` | rgb(220, 38, 38) | Errors, emergency |
| Danger Light | `#ef4444` | rgb(239, 68, 68) | Error hover |

### Neutral Colors (Grays)
| Name | Hex Code | RGB | Usage |
|------|----------|-----|-------|
| White | `#ffffff` | rgb(255, 255, 255) | Backgrounds, cards |
| Gray 50 | `#f8fafc` | rgb(248, 250, 252) | Light backgrounds |
| Gray 100 | `#f1f5f9` | rgb(241, 245, 249) | Input backgrounds |
| Gray 200 | `#e2e8f0` | rgb(226, 232, 240) | Borders, dividers |
| Gray 300 | `#cbd5e1` | rgb(203, 213, 225) | Disabled states |
| Gray 400 | `#94a3b8` | rgb(148, 163, 184) | Placeholder text |
| Gray 500 | `#64748b` | rgb(100, 116, 139) | Muted text |
| Gray 600 | `#475569` | rgb(71, 85, 105) | Secondary text |
| Gray 700 | `#334155` | rgb(51, 65, 85) | Body text |
| Gray 800 | `#1e293b` | rgb(30, 41, 59) | Headings |
| Gray 900 | `#0f172a` | rgb(15, 23, 42) | Dark text |

### Background Colors
| Name | Hex Code | Usage |
|------|----------|-------|
| Page Background | `#f5f7fa` | Main page background |
| Card Background | `#ffffff` | Cards, modals |
| Input Background | `#f8fafc` | Form inputs, chat input area |
| Overlay | `rgba(0, 0, 0, 0.5)` | Modal overlays |

### Gradient Definitions
```css
/* Primary Navy Gradient */
background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);

/* Active/Recording State */
background: linear-gradient(135deg, #2563eb 0%, #1e3a5f 100%);

/* Success Gradient */
background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);

/* Muted/Disabled Gradient */
background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);

/* User Message Gradient */
background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
```

---

## Typography

### Font Families
```css
/* Primary Font (English) */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Urdu/Arabic Font */
font-family: 'Noto Sans Arabic', 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', sans-serif;

/* Monospace (Code) */
font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
```

### Font Sizes
| Element | Size | Line Height | Weight |
|---------|------|-------------|--------|
| H1 | 1.75em (28px) | 1.3 | 600 |
| H2 | 1.5em (24px) | 1.35 | 600 |
| H3 | 1.25em (20px) | 1.4 | 600 |
| H4 | 1.125em (18px) | 1.45 | 600 |
| Body Large | 16px | 1.6 | 400 |
| Body | 15px | 1.7 | 400 |
| Body Small | 14px | 1.5 | 400 |
| Caption | 13px | 1.4 | 500 |
| Tiny | 12px | 1.4 | 400 |

### Urdu Typography
| Element | Size | Line Height | Direction |
|---------|------|-------------|-----------|
| Urdu Body | 18px | 2.0 | RTL |
| Urdu Message | 17px | 1.8 | RTL |
| Urdu Segment | 1.15em | 1.9 | RTL |
| Urdu Chip | 15px | 1.6 | RTL |

### Font Weights
| Name | Value | Usage |
|------|-------|-------|
| Regular | 400 | Body text |
| Medium | 500 | Labels, captions |
| Semibold | 600 | Headings, emphasis |
| Bold | 700 | Titles, strong emphasis |

---

## Buttons

### Primary Button
```css
.btn-primary {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
}
```

### Secondary Button (Outline)
```css
.btn-secondary {
    background: transparent;
    color: #1e3a5f;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    border: 2px solid #1e3a5f;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-secondary:hover {
    background: #1e3a5f;
    color: white;
}
```

### Ghost Button (Header/Transparent)
```css
.btn-ghost {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-ghost:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
}
```

### Icon Button (Square)
```css
.btn-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    transition: all 0.2s ease;
}

/* Light variant */
.btn-icon-light {
    background: #f1f5f9;
    color: #475569;
}

.btn-icon-light:hover {
    background: #e2e8f0;
    color: #1e3a5f;
}

/* Primary variant */
.btn-icon-primary {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
    color: white;
}

.btn-icon-primary:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
}
```

### Danger Button
```css
.btn-danger {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
}

.btn-danger:hover {
    background: #dc2626;
    color: white;
    border-color: #dc2626;
}
```

### Success Button
```css
.btn-success {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    color: white;
    padding: 10px 16px;
    border-radius: 50px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    box-shadow: 0 4px 16px rgba(34, 197, 94, 0.35);
}

.btn-success:hover {
    transform: scale(1.05);
}
```

### Button Sizes
| Size | Padding | Font Size | Border Radius |
|------|---------|-----------|---------------|
| Small | 6px 12px | 12px | 6px |
| Medium | 8px 16px | 13px | 8px |
| Default | 12px 24px | 15px | 8px |
| Large | 14px 28px | 16px | 10px |
| Icon SM | 36x36px | 14px | 10px |
| Icon Default | 44x44px | 18px | 12px |

---

## Cards & Containers

### Standard Card
```css
.card {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 
                0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
```

### Elevated Card
```css
.card-elevated {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.08);
}
```

### Bordered Card
```css
.card-bordered {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px;
}
```

### Interactive Card (Chip)
```css
.card-interactive {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.card-interactive:hover {
    background: #e8f0f8;
    border-color: #1e3a5f;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(30, 58, 95, 0.1);
}
```

### Header Container
```css
.header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

### Message Bubble
```css
/* User Message */
.message-bubble-user {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
    color: white;
    padding: 14px 18px;
    border-radius: 18px;
    border-bottom-right-radius: 4px;
    max-width: 80%;
}

/* Bot Message - Plain (no bubble) */
.message-plain {
    font-size: 15px;
    line-height: 1.7;
    color: #1e293b;
}
```

---

## Form Elements

### Text Input
```css
.input-text {
    width: 100%;
    padding: 12px 16px;
    font-size: 15px;
    line-height: 1.5;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    color: #1e293b;
    transition: all 0.2s ease;
}

.input-text::placeholder {
    color: #94a3b8;
}

.input-text:focus {
    outline: none;
    border-color: #1e3a5f;
    box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}
```

### Textarea
```css
.textarea {
    width: 100%;
    min-height: 100px;
    padding: 12px 16px;
    font-size: 15px;
    line-height: 1.6;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    background: #ffffff;
    resize: vertical;
    transition: all 0.2s ease;
}

.textarea:focus {
    outline: none;
    border-color: #1e3a5f;
    box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}
```

### Input Container (Chat Style)
```css
.input-container {
    display: flex;
    gap: 12px;
    align-items: flex-end;
    background: #ffffff;
    border: 2px solid #e2e8f0;
    border-radius: 16px;
    padding: 8px 8px 8px 16px;
    transition: all 0.2s ease;
}

.input-container:focus-within {
    border-color: #1e3a5f;
    box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}
```

### Select Dropdown
```css
.select {
    padding: 12px 40px 12px 16px;
    font-size: 15px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff url('data:image/svg+xml,...') no-repeat right 12px center;
    appearance: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.select:focus {
    outline: none;
    border-color: #1e3a5f;
    box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}
```

---

## Shadows & Elevation

### Shadow Levels
```css
/* Level 0 - Flat */
box-shadow: none;

/* Level 1 - Subtle */
box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

/* Level 2 - Small */
box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 
            0 1px 2px 0 rgba(0, 0, 0, 0.06);

/* Level 3 - Medium (Cards) */
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 
            0 2px 4px -1px rgba(0, 0, 0, 0.06);

/* Level 4 - Large */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 
            0 4px 6px -2px rgba(0, 0, 0, 0.05);

/* Level 5 - XL (Modals) */
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 
            0 10px 10px -5px rgba(0, 0, 0, 0.04);

/* Soft Shadow (Main containers) */
box-shadow: 0 0 40px rgba(0, 0, 0, 0.08);

/* Colored Shadow - Primary */
box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);

/* Colored Shadow - Success */
box-shadow: 0 4px 16px rgba(34, 197, 94, 0.35);

/* Colored Shadow - Muted */
box-shadow: 0 4px 16px rgba(107, 114, 128, 0.35);
```

---

## Animations & Transitions

### Transition Durations
| Speed | Duration | Usage |
|-------|----------|-------|
| Fast | 0.15s | Micro-interactions |
| Normal | 0.2s | Buttons, inputs |
| Medium | 0.3s | Cards, overlays |
| Slow | 0.5s | Page transitions |

### Standard Transitions
```css
/* Default transition */
transition: all 0.2s ease;

/* Transform only */
transition: transform 0.2s ease;

/* Color transitions */
transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;

/* Opacity */
transition: opacity 0.3s ease;
```

### Animation Keyframes

#### Pulse Animation
```css
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* Usage */
animation: pulse 1.5s infinite;
```

#### Status Pulse (Online indicator)
```css
@keyframes statusPulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(0.9); }
}

/* Usage */
animation: statusPulse 2s infinite;
```

#### Message Slide In
```css
@keyframes messageSlide {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Usage */
animation: messageSlide 0.3s ease;
```

#### Typing Bounce
```css
@keyframes typing-bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}

/* Usage for 3 dots */
.dot:nth-child(1) { animation: typing-bounce 1.4s infinite ease-in-out; animation-delay: -0.32s; }
.dot:nth-child(2) { animation: typing-bounce 1.4s infinite ease-in-out; animation-delay: -0.16s; }
.dot:nth-child(3) { animation: typing-bounce 1.4s infinite ease-in-out; animation-delay: 0s; }
```

#### Audio Playing
```css
@keyframes audioPlaying {
    0% { opacity: 0.6; transform: scale(1); }
    100% { opacity: 1; transform: scale(1.1); }
}

/* Usage */
animation: audioPlaying 0.5s ease-in-out infinite alternate;
```

### Hover Transforms
```css
/* Lift effect */
transform: translateY(-2px);

/* Scale effect */
transform: scale(1.05);

/* Combined */
transform: translateY(-1px) scale(1.02);
```

---

## Spacing System

### Base Unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Tight spacing |
| space-2 | 8px | Icon gaps, small padding |
| space-3 | 12px | Button gaps, input padding |
| space-4 | 16px | Card padding, section gaps |
| space-5 | 20px | Large gaps |
| space-6 | 24px | Container padding |
| space-8 | 32px | Section spacing |
| space-10 | 40px | Large sections |
| space-12 | 48px | Page sections |
| space-16 | 64px | Major sections |

### Common Paddings
```css
/* Buttons */
padding: 8px 14px;   /* Small */
padding: 12px 24px;  /* Default */
padding: 14px 28px;  /* Large */

/* Cards */
padding: 16px;       /* Compact */
padding: 24px;       /* Default */

/* Containers */
padding: 20px 24px;  /* Header */
padding: 24px;       /* Chat area */

/* Inputs */
padding: 12px 16px;  /* Default */
padding: 8px 8px 8px 16px; /* Chat input container */
```

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| radius-sm | 4px | Small elements, tags |
| radius | 6px | Buttons, small cards |
| radius-md | 8px | Inputs, buttons |
| radius-lg | 12px | Cards, avatars |
| radius-xl | 16px | Large cards, containers |
| radius-2xl | 18px | Message bubbles |
| radius-3xl | 20px | Badges |
| radius-full | 50px / 50% | Pills, circles |

### Specific Radii
```css
/* Message bubble (user) */
border-radius: 18px;
border-bottom-right-radius: 4px;

/* Avatar */
border-radius: 12px;

/* Icon button */
border-radius: 12px;

/* Input container */
border-radius: 16px;

/* Pill/Badge */
border-radius: 50px;

/* Circle */
border-radius: 50%;
```

---

## Icons

### Icon Library
**Font Awesome 6** (fas = solid, far = regular, fab = brands)

### Common Icons Used
| Icon | Class | Usage |
|------|-------|-------|
| Robot | `fas fa-robot` | AI/Bot avatar |
| User | `fas fa-user` | User avatar |
| Microphone | `fas fa-microphone` | Voice input |
| Paper Plane | `fas fa-paper-plane` | Send message |
| Volume Up | `fas fa-volume-up` | Audio/TTS |
| Volume Mute | `fas fa-volume-mute` | Muted state |
| Clock | `fas fa-clock` | Timestamp |
| Trash | `fas fa-trash` | Delete/Clear |
| Globe | `fas fa-globe` | Language |
| Info Circle | `fas fa-info-circle` | Information |
| Exclamation Triangle | `fas fa-exclamation-triangle` | Warning |
| Check Circle | `fas fa-check-circle` | Success |
| Times Circle | `fas fa-times-circle` | Error |
| Phone | `fas fa-phone` | Emergency call |
| Pills | `fas fa-pills` | Medicines |
| Stethoscope | `fas fa-stethoscope` | Doctors |
| Calendar | `fas fa-calendar-alt` | Appointments |

### Icon Sizes
| Size | Font Size | Usage |
|------|-----------|-------|
| XS | 11px | Badges |
| SM | 12px | Inline with text |
| Default | 14px | Buttons, labels |
| MD | 16px | Standalone icons |
| LG | 18px | Large buttons |
| XL | 20px | Avatars |
| 2XL | 24px | Headers |

---

## Responsive Breakpoints

### Breakpoint Values
| Name | Width | Usage |
|------|-------|-------|
| xs | < 480px | Mobile small |
| sm | < 640px | Mobile |
| md | < 768px | Tablet portrait |
| lg | < 992px | Tablet landscape |
| xl | < 1200px | Desktop |
| 2xl | >= 1200px | Large desktop |

### Media Query Examples
```css
/* Tablet and below */
@media (max-width: 992px) {
    .header-features { display: none !important; }
    .assistant-page { min-height: calc(100vh - 60px); }
}

/* Mobile */
@media (max-width: 768px) {
    .chat-header { padding: 16px; }
    .chat-messages { padding: 16px; min-height: 300px; }
    .sample-grid { grid-template-columns: 1fr; }
    .bottom-bar-inner { flex-direction: column; }
}

/* Small mobile */
@media (max-width: 480px) {
    .assistant-icon { width: 40px; height: 40px; }
    .assistant-title { font-size: 16px; }
    .tts-toggle-inner span { display: none; }
}
```

---

## Component Quick Reference

### Avatar
```css
.avatar {
    width: 40px;
    height: 40px;
    min-width: 40px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
}

.avatar-bot {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
    color: white;
}

.avatar-user {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: white;
}
```

### Status Indicator
```css
.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
    animation: statusPulse 2s infinite;
}
```

### Badge/Pill
```css
.badge {
    background: rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.9);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}
```

### Typing Indicator
```css
.typing-dots {
    display: flex;
    gap: 6px;
    padding: 8px 0;
}

.typing-dots span {
    width: 10px;
    height: 10px;
    background-color: #1e3a5f;
    border-radius: 50%;
}
```

---

## CSS Variables (Optional)

```css
:root {
    /* Colors */
    --color-primary: #1e3a5f;
    --color-primary-dark: #0f2744;
    --color-primary-light: #2d4a6f;
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-danger: #dc2626;
    
    /* Grays */
    --color-gray-50: #f8fafc;
    --color-gray-100: #f1f5f9;
    --color-gray-200: #e2e8f0;
    --color-gray-400: #94a3b8;
    --color-gray-500: #64748b;
    --color-gray-700: #334155;
    --color-gray-800: #1e293b;
    --color-gray-900: #0f172a;
    
    /* Typography */
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-urdu: 'Noto Sans Arabic', 'Noto Nastaliq Urdu', sans-serif;
    --font-mono: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
    
    /* Spacing */
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-6: 24px;
    
    /* Radius */
    --radius-sm: 4px;
    --radius: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-2xl: 18px;
    --radius-full: 50px;
    
    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 0 40px rgba(0, 0, 0, 0.08);
    --shadow-primary: 0 4px 12px rgba(30, 58, 95, 0.3);
    
    /* Transitions */
    --transition-fast: 0.15s ease;
    --transition: 0.2s ease;
    --transition-slow: 0.3s ease;
}
```

---

*Last Updated: December 2024*
*Design System Version: 1.0*

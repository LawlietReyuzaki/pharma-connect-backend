# Red Dot Pharmacy - Navy Blue Glassmorphism Design Guidelines

## Design Approach
**Theme**: Navy Blue with Glassmorphism Effects
**Framework**: Bootstrap 5 with Custom CSS
**Inspiration**: Modern healthcare apps with frosted glass UI elements
**Principles**: Clean, professional, accessible, modern aesthetics

## Color Palette

### Primary Colors
- **Navy Blue**: #1e3a5f (Primary brand color)
- **Navy Dark**: #0f2744 (Darker variant for headers, footers)
- **Navy Light**: #e8f0f8 (Light backgrounds, highlights)
- **Accent Blue**: #2563eb (Buttons, interactive elements)
- **Accent Light**: #3b82f6 (Hover states, glows)

### Neutral Colors
- **Gray 50**: #f8fafc (Lightest backgrounds)
- **Gray 100**: #f1f5f9 (Section backgrounds)
- **Gray 200**: #e2e8f0 (Borders, dividers)
- **Gray 300**: #cbd5e1 (Disabled states)
- **Gray 400**: #94a3b8 (Placeholder text)
- **Gray 500**: #64748b (Secondary text)
- **Gray 600**: #475569 (Body text)
- **Gray 700**: #334155 (Headings)
- **Gray 800**: #1e293b (Dark text)
- **Gray 900**: #0f172a (Darkest text, footer)

### Semantic Colors
- **Success**: #10b981 (Green - confirmations, in-stock)
- **Warning**: #f59e0b (Amber - alerts, pending)
- **Danger**: #ef4444 (Red - errors, out-of-stock)
- **Info**: #0ea5e9 (Cyan - informational)

## Glassmorphism Effects

### Glass Card
```css
background: rgba(255, 255, 255, 0.7);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid rgba(255, 255, 255, 0.3);
box-shadow: 0 8px 32px rgba(30, 58, 95, 0.15);
```

### Glass Card Hover
```css
background: rgba(255, 255, 255, 0.85);
border-color: rgba(37, 99, 235, 0.3);
box-shadow: 0 12px 32px rgba(30, 58, 95, 0.18), 0 0 40px rgba(37, 99, 235, 0.15);
```

### Dark Glass (Headers, Modals)
```css
background: rgba(30, 58, 95, 0.85);
backdrop-filter: blur(16px);
```

## Typography
- **Primary Font**: Inter (Google Fonts) - clean, modern sans-serif
- **Display Font**: Poppins (Google Fonts) - headings, titles
- **Hierarchy**:
  - Page Titles: 2.75rem (44px), font-weight 800
  - Section Headers: 1.5rem (24px), font-weight 700
  - Card Titles: 1.125rem (18px), font-weight 600
  - Body Text: 1rem (16px), font-weight 400
  - Helper Text: 0.875rem (14px), font-weight 400

## Layout System
- **Spacing Scale**: 4px base unit (0.25rem increments)
- **Component Padding**: 20-32px standard
- **Section Padding**: 80-100px vertical
- **Border Radius**: 
  - Small: 8px
  - Medium: 12px
  - Large: 16px
  - XL: 24px
  - Full: 9999px (pills, badges)

## Component Styles

### Buttons
- **Primary**: Navy gradient background, white text
- **Secondary**: Transparent with navy border
- **Hover**: Lift effect (translateY -2px), enhanced shadow with glow

### Cards
- **Background**: Glass effect (70% white with blur)
- **Border**: 1px subtle white/glass border
- **Hover**: Enhanced glass, blue glow effect
- **Shadow**: Soft navy-tinted shadows

### Form Elements
- **Inputs**: 2px border, rounded corners
- **Focus State**: Navy border with blue glow ring
- **Labels**: 600 weight, gray-700 color

### Navigation
- **Navbar**: Navy gradient with blur
- **Links**: White/translucent, smooth transitions
- **Active State**: Subtle white background

## Animations
- **Transition Fast**: 0.15s ease (micro-interactions)
- **Transition Base**: 0.25s ease (standard transitions)
- **Transition Slow**: 0.4s ease (larger movements)
- **Hover Lift**: translateY(-4px to -8px)
- **Glow Pulse**: Subtle blue glow animations on hero elements

## Icons
**Font Awesome 6**: Consistent icon system
- Navigation: 18px
- Buttons: 16px
- Inline: 14px

## Responsive Breakpoints
- Desktop: 1200px+
- Tablet: 768px - 1199px
- Mobile: < 768px

## Best Practices
1. Always use glass effects on cards over gradient/colored backgrounds
2. Maintain contrast ratios for accessibility (WCAG AA)
3. Use subtle shadows to create depth hierarchy
4. Add blue glow on interactive element focus/hover
5. Keep animations subtle and performant

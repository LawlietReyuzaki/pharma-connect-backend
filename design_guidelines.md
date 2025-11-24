# Red Dot Pharmacy Admin Panel - Design Guidelines

## Design Approach
**Framework**: Bootstrap 5 Healthcare Admin Dashboard
**Inspiration**: Modern medical portals (Epic MyChart, Athenahealth) with enterprise admin patterns
**Principles**: Data clarity, efficient workflows, professional medical aesthetic

## Typography
- **Primary Font**: Inter (Google Fonts) - clean, highly legible for data
- **Hierarchy**:
  - Page Titles: 28px, font-weight 600
  - Section Headers: 20px, font-weight 600
  - Table Headers: 14px, font-weight 700, uppercase, letter-spacing 0.5px
  - Body/Data: 15px, font-weight 400
  - Helper Text: 13px, font-weight 400

## Layout System
**Spacing Primitives**: Tailwind equivalents of Bootstrap's spacing (0.25rem increments)
- Primary rhythm: 16px (1rem), 24px (1.5rem), 32px (2rem)
- Component padding: 20px standard, 32px for cards
- Section spacing: 40px between major sections

## Core Layout Structure

### Sidebar Navigation (Fixed Left)
- Width: 260px on desktop, collapsible to 70px icon-only
- Contains: Logo at top, navigation menu (Dashboard, Doctors, Availability, Patients, Reports), logout at bottom
- Icons: Font Awesome (fa-calendar-check, fa-user-md, fa-chart-line, etc.)
- Active state: Bold text with subtle background indicator

### Main Content Area
- Left margin: 260px (accounts for sidebar)
- Max-width: 1400px with auto margins for ultra-wide screens
- Top bar: Breadcrumb navigation + page title + primary action button (right-aligned)
- Content padding: 32px all sides

## Component Library

### Data Table (Doctor Schedule Display)
- Full-width responsive table with alternating row backgrounds
- **Columns**: Doctor Name | Specialty | Day of Week | Time Range | Status | Actions
- Column widths: Doctor (20%), Specialty (15%), Day (12%), Time (20%), Status (10%), Actions (10%)
- Row height: 56px for comfortable scanning
- Status badges: Small rounded pills (Available/Unavailable/On Leave)
- Action buttons: Icon-only for edit (fa-edit) and delete (fa-trash-alt), 36px × 36px, positioned together with 8px gap
- Pagination: Bottom-right, showing "10 of 243 entries" with prev/next controls

### Forms (Add/Edit Availability)
**Modal or Card-Based Form**:
- Doctor Selection: Searchable dropdown with avatar + name + specialty
- Day Selector: Radio button group or button group (Mon-Sun) in horizontal layout
- Time Range: Two time pickers side-by-side (Start Time | End Time) with colon separator visual
- Notes field: Textarea (3 rows, optional context)
- Action buttons: Primary "Save Availability" + Secondary "Cancel" (right-aligned, 16px gap)
- Form field spacing: 24px vertical gap between fields
- Label positioning: Above inputs, 8px margin-bottom

### Quick Add Widget (Dashboard Integration)
- Compact card: 340px width
- Contains: Mini form with doctor dropdown + day + single time range
- "Quick Add" button at bottom, full-width
- Background: Slightly elevated card with 4px border-left accent

### Filter Controls
- Horizontal bar above table with inline filters:
  - Doctor filter (dropdown)
  - Day filter (multi-select chips)
  - Date range picker
  - Search input (right-aligned, 280px width)
- 16px spacing between filter elements

### Empty States
- When no schedules: Centered illustration area (200px height) with "No availability schedules found" + "Add New Schedule" CTA button below
- Icon: fa-calendar-plus at 48px size

## Responsive Behavior
- **Desktop (≥992px)**: Full sidebar + table with all columns
- **Tablet (768-991px)**: Collapsed icon-only sidebar, condensed table (hide Specialty column)
- **Mobile (<768px)**: Off-canvas sidebar, card-based schedule view instead of table (each schedule = card with stacked info)

## Data Visualization
- Weekly calendar grid view toggle: Alternative to table showing doctor availability in calendar format
- Grid: 7 columns (days) with time slots as rows
- Doctor assignments shown as colored blocks within time slots
- Toggle button: Top-right of main content area (Table View | Calendar View)

## Icons Implementation
**Font Awesome CDN** (v6):
- Navigation: fa-calendar-check, fa-user-md, fa-users, fa-chart-line, fa-cog
- Actions: fa-edit, fa-trash-alt, fa-plus-circle, fa-filter
- Status: fa-check-circle, fa-clock, fa-user-times
- Size: 18px for navigation, 16px for action buttons, 14px for inline status

## Images
**No hero image required** - This is a functional admin panel, not a marketing page. Focus on data density and workflow efficiency.
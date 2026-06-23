# CFGI Brand Identity Reference

> Format-agnostic brand standards extracted from the CFGI Brand Style Guide (January 2025).
> Apply these values to any output — Word documents, HTML reports, Excel models, email templates, etc.

---

## Colors

### Primary Colors

| Name | Hex | Primary Use |
|------|-----|-------------|
| Navy Blue | `#002A5C` | Titles, headers, section dividers, table headers |
| Dark Navy | `#000D1C` | Dark backgrounds, high-contrast contexts |
| Murrey | `#9A0B52` | Accent, highlights, calls-to-action |

### Secondary Colors

| Name | Hex | Light Variant | Use |
|------|-----|---------------|-----|
| Teal Green | `#51C69E` | `#A8E3CF` | Supporting accent, positive indicators |
| Green | `#066173` | `#83B0B9` | Supporting accent, secondary charts |

### Extended Palette (charts, diagrams, callouts)

| Name | Hex | Light Variant |
|------|-----|---------------|
| Medium Blue | `#277FBB` | — |
| Light Blue | `#4AC7FF` | — |
| Yellow | `#FFDA3D` | `#FFED9E` |
| Orange | `#FFBF3D` | `#FFDF9E` |
| Purple | `#5F4EB5` | `#AFA7DA` |
| Red | `#C83A20` | `#E49D90` |

### Neutrals

| Name | Hex | Use |
|------|-----|-----|
| Main Text | `#3D454E` | All body text |
| Secondary Gray | `#999FA4` | Captions, footnotes, secondary labels |
| Light Gray | `#D5DADE` | Borders, dividing rules |
| Light Background | `#F5F8FB` | Page/section backgrounds, alternating table rows |
| White | `#FFFFFF` | Reversed text, card backgrounds |

### Chart Color Sequence

When multiple series are needed, apply colors in this order:

1. `#002A5C` Navy Blue
2. `#277FBB` Medium Blue
3. `#4AC7FF` Light Blue
4. `#51C69E` Teal Green
5. `#9A0B52` Murrey
6. `#066173` Green
7. `#FFDA3D` Yellow
8. `#FFBF3D` Orange
9. `#5F4EB5` Purple
10. `#C83A20` Red

### Transparency / Overlays

| Base Color | Opacity | Use |
|------------|---------|-----|
| Medium Blue `#277FBB` | 5% (95% transparent) | Subtle blue overlay on images |
| Navy Blue `#002A5C` | 5% (95% transparent) | Subtle dark overlay on images |

---

## Typography

### Typefaces

| Role | Font | Notes |
|------|------|-------|
| Headings / Display | **Georgia** | Serif; use for all titles, section headers, prominent labels |
| Body / UI | **Arial** | Sans-serif; use for all body copy, captions, data labels, table text |

Georgia and Arial are the only approved CFGI typefaces. Do not substitute with other fonts even when Georgia or Arial are unavailable by default — embed or specify fallbacks rather than accepting a different face.

### Type Scale

| Level | Size | Font | Weight | Color |
|-------|------|------|--------|-------|
| Page/slide title | 24pt | Georgia | Regular | Navy `#002A5C` |
| Section heading (H1) | 18pt | Georgia or Arial | Bold | Navy `#002A5C` |
| Subheading (H2) | 16pt | Arial | Bold | Navy `#002A5C` or Main Text `#3D454E` |
| Body / Level 3 | 14pt | Arial | Regular | Main Text `#3D454E` |
| Small body / Level 4 | 12pt | Arial | Regular | Main Text `#3D454E` |
| Captions / footnotes | 11pt | Arial | Regular | Secondary Gray `#999FA4` |

### Title Styling Rule

Titles are set in **ALL CAPS** with **3pt letter-spacing**. Apply this treatment to any primary document title or section cover heading regardless of medium.

### Text Color Rules

- Default body text: `#3D454E` (Main Text)
- Headings: `#002A5C` (Navy Blue)
- Captions, footer lines, secondary labels: `#999FA4` (Secondary Gray)
- Reversed text (on dark backgrounds): `#FFFFFF`
- Hyperlinks: `#5F4EB5` (Purple)

### Bullets

- Bullet color: `#277FBB` (Medium Blue)
- Bullet font: Arial
- Do not use decorative unicode bullets; use standard list markers styled to the bullet color

---

## Core Brand Rules

**Hierarchy is always Navy → Body Gray → Secondary Gray.** Titles anchor in Navy; body content runs in Main Text gray; supporting/metadata text drops to Secondary Gray. Never use black (`#000000`) as a text color.

**Headings use Georgia; everything else uses Arial.** The serif/sans-serif split is intentional and consistent. Mixing additional typefaces breaks the identity.

**White space is structure.** CFGI layouts rely on generous margins and breathing room rather than borders and boxes to create separation. Avoid cramming content.

**Accent colors are accents.** Murrey (`#9A0B52`), Teal (`#51C69E`), and the extended palette exist for emphasis — icons, callout boxes, chart series, status indicators. They should never dominate a page or become the default text color.

**Light Background (`#F5F8FB`) as surface.** Use this very light blue-gray as an alternative to white for content area fills, alternating table rows, or sidebar backgrounds. It keeps documents from feeling flat without introducing color noise.

**Footer / copyright line.** Any externally facing CFGI document should carry the line: `© CFGI | ALL RIGHTS RESERVED`. Set in Secondary Gray (`#999FA4`), Arial, ~10–11pt.

---

## Tables

| Element | Style |
|---------|-------|
| Header row background | Navy Blue `#002A5C` |
| Header row text | White `#FFFFFF`, Arial, Bold |
| Alternating row fill | Light Background `#F5F8FB` / White `#FFFFFF` |
| Body text | Arial, 11–12pt, Main Text `#3D454E` |
| Border / divider lines | Light Gray `#D5DADE` |

---

## Callouts & Highlights

| Type | Background | Text | Border / Accent |
|------|------------|------|-----------------|
| Key stat / KPI box | Light Background `#F5F8FB` | Navy `#002A5C` | Left rule in Medium Blue `#277FBB` |
| Important callout | Navy `#002A5C` | White `#FFFFFF` | — |
| Warning / caution | Orange light `#FFDF9E` | Main Text `#3D454E` | Orange `#FFBF3D` |
| Positive indicator | Teal light `#A8E3CF` | Main Text `#3D454E` | Teal `#51C69E` |
| Negative indicator | Red light `#E49D90` | Main Text `#3D454E` | Red `#C83A20` |

---

## Quick-Reference Hex List

```
/* Primary */
--cfgi-navy:          #002A5C;
--cfgi-dark-navy:     #000D1C;
--cfgi-murrey:        #9A0B52;

/* Secondary */
--cfgi-teal:          #51C69E;
--cfgi-teal-light:    #A8E3CF;
--cfgi-green:         #066173;
--cfgi-green-light:   #83B0B9;

/* Extended */
--cfgi-blue-mid:      #277FBB;
--cfgi-blue-light:    #4AC7FF;
--cfgi-yellow:        #FFDA3D;
--cfgi-yellow-light:  #FFED9E;
--cfgi-orange:        #FFBF3D;
--cfgi-orange-light:  #FFDF9E;
--cfgi-purple:        #5F4EB5;
--cfgi-purple-light:  #AFA7DA;
--cfgi-red:           #C83A20;
--cfgi-red-light:     #E49D90;

/* Neutrals */
--cfgi-text:          #3D454E;
--cfgi-gray-mid:      #999FA4;
--cfgi-gray-light:    #D5DADE;
--cfgi-bg-light:      #F5F8FB;
--cfgi-white:         #FFFFFF;
```

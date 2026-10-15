# WebAwesome brand kit

For developers building pages, plugins, emails or documents for WebAwesome (webawesome.co.uk).
Tagline: **Digital products · Real impact**

## What is in this kit

| File | Use |
|---|---|
| `tokens/tokens.css` | CSS variables (light and dark), base styles and button classes. Copy into any project. |
| `tokens/theme-palette.json` | Palette, gradient, fonts, font sizes and layout for the WordPress block theme `theme.json`. |
| `logo/logo-mark.svg` | Master logo. Use this for the web. |
| `logo/logo-mark-1024.png` ... `-64.png` | Transparent PNG exports for documents, social and email. |
| `logo/favicon-32.png`, `logo/apple-touch-icon-180.png` | Favicon and iOS home screen icon. |

## Logo

A rounded square in deep violet with a gradient frame. Inside, a cyan W ribbon and a pink A ribbon meet at a small cyan diamond.

- Always use the supplied files. Do not redraw, recolour, stretch, outline, add shadows, remove the frame or swap the ribbons.
- Clear space: one quarter of the mark's width on every side.
- Minimum size: 32 px wide on screen, 10 mm in print.
- Backgrounds: white, Mist, Midnight, Deep Night. On photos, place the mark on a solid tile.
- Emails and documents: use `logo-mark-256.png` (shown at 64 to 96 px). Do not hot-link the SVG in email.
- Stacked lockup (suggested): mark with WEBAWESOME below in Space Grotesk 700, capitals, letter-spacing 0.22em, white on dark.

## Colour

| Name | Hex | Use | Contrast |
|---|---|---|---|
| Royal Violet | `#3B1A88` | Primary buttons, links | White text 12.4:1 |
| Midnight | `#0B1642` | Text, dark surfaces | 16.0:1 on Mist |
| Electric Violet | `#8E4DFF` | Icons, borders | White text 4.5:1, large text only |
| Neon Cyan | `#00E5FF` | Highlights on dark | Midnight text on it 11.3:1. Never text on light (1.4:1) |
| Hot Pink | `#FF4DA6` | Accent button | Midnight text on it 5.7:1. White text fails (3.1:1) |
| Mist | `#F6F4FF` | Page background | Derived |
| Muted | `#5B5680` | Secondary text | 6.3:1 on Mist. Derived |
| Lilac Line | `#E3DDF6` | Borders | Derived |
| Deep Night | `#060B2B` | Dark background | Derived |
| White | `#FFFFFF` | Cards | |

**Logo Beam gradient:** `linear-gradient(135deg, #00D9FF 0%, #8E4DFF 45%, #FF4DA6 100%)`.
Use it once per screen (a hero rule, one button or one card edge). Never behind body text.

**Dark mode:** background Deep Night, surface Midnight, border `#26306B`, muted text `#A7A6D1`, links `#B895FF` (8.1:1).

"Derived" means the value was chosen for this kit to complement the logo colours. The other colours come directly from the logo file.

## Typography

| Role | Font | Weights | Notes |
|---|---|---|---|
| Headings | Space Grotesk | 500, 600, 700 | Weight 600, line-height 1.06, letter-spacing -0.03em |
| Body and UI | Inter | 400, 500, 600 | 1.0625 rem, line-height 1.7 |
| Labels, code, figures | IBM Plex Mono | 400, 600 | Uppercase labels: 0.75 rem, letter-spacing 0.12em |

Google Fonts:
```
https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap
```
Where web fonts cannot load (Word, some email clients) use Arial for body and a bold sans for headings.

Sizes: display `clamp(2.75rem, 1.8rem + 4.8vw, 5.9rem)`, H2 `clamp(2rem, 1.5rem + 2.6vw, 3.6rem)`, H3 `clamp(1.35rem, 1.2rem + 0.9vw, 1.9rem)`, lead `clamp(1.125rem, 1.05rem + 0.4vw, 1.3rem)`, body `1.0625rem`, small `0.875rem`.
Spacing steps: 0.5, 1, 1.75, 3, 5 rem. Reading column 720 px, wide layout 1280 px.

## Components

- **Buttons:** Inter 600, 0.95 rem, 10 px radius. Default is Royal Violet with white text. Secondary is transparent with a Lilac Line border. Accent is Hot Pink with Midnight text. At most one gradient or accent button per screen.
- **Links:** Royal Violet. Midnight on hover.
- **Cards:** white (Midnight in dark mode), 1 px Lilac Line border, 14 px radius. Avoid stacking border, fill and shadow on every block.

## Using it

**Any website or app:** include the Google Fonts link, then `tokens/tokens.css`. Use `var(--wa-royal-violet)` and the other `--wa-*` variables, or the `.wa-btn` classes.

**WordPress block theme (WebAwesome X):** merge `tokens/theme-palette.json` into `theme.json`. Colours become `var(--wp--preset--color--royal-violet)` and so on. Update the logo in Site Identity with `logo-mark.svg` and the site icon with `logo-mark-512.png`.

**Email and documents:** use hex values directly and the 256 px PNG for the logo.

## Voice

Practical, clear, on the client's side. Lead with the client's problem, then the result, and name concrete outcomes. UK spelling and £. Avoid hype words, unexplained jargon, unmeasurable promises, emoji headings and stacked exclamation marks.
Contact: hello@webawesome.co.uk

## Checks before shipping

1. Text contrast meets 4.5:1 (small) or 3:1 (large) using the table above.
2. The gradient appears once per screen.
3. Only Space Grotesk, Inter and IBM Plex Mono are used.
4. The logo is unaltered and has clear space.

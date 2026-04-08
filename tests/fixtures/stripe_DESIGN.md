# Stripe Design System (test fixture)

A trimmed-down DESIGN.md sample used by the design_md test suite. This file is
intentionally minimal but still contains the 9 canonical H2 sections.

## Visual Theme & Atmosphere

Stripe projects a calm, technical, premium atmosphere. Soft gradients, deep
navy backgrounds, and abundant whitespace make the product feel trustworthy
and developer-friendly.

## Color Palette & Roles

### Primary
- **Stripe Purple** (`#533afd`): Primary brand color, CTA backgrounds, and key accents.
- **Deep Navy** (`#061b31`): Primary heading color and dark hero backgrounds.
- **Cloud White** (`#ffffff`): Page background and surface base for cards.

### Neutral
- **Slate Gray** (`#425466`): Body text and secondary UI elements.
- **Marketing Black** (`#010102` / `#08090a`): Hero background duo, near-pure with a cool undertone.
- **Smoke** (`rgba(0,0,0,0.95)` / `#000000f2`): Overlay and modal scrim with soft transparency.

## Typography Rules

- Display: Sohne 56px / 64px line-height, weight 600.
- Headings (H1): Sohne 40px / 48px, weight 600.
- Body: Inter 16px / 24px, weight 400.
- Monospace: Sohne Mono 14px / 22px for code blocks.

## Component Stylings

Buttons use a 6px radius, 16px horizontal padding, and a subtle inner gradient
on hover. Cards have 12px radius, soft shadows, and a 1px slate-200 border.

## Layout Principles

12-column grid, 1280px max-content width, 80px section vertical rhythm,
generous gutters of 24px on desktop and 16px on mobile.

## Depth & Elevation

Three elevation tiers: flat (no shadow), card (0 1px 2px rgba(0,0,0,0.06)),
and floating (0 8px 24px rgba(6,27,49,0.12)). No drop shadows on dark mode.

## Do's and Don'ts

- Do: Use generous whitespace and align everything to the 12-column grid.
- Don't: Stack more than two purples side-by-side.
- Do: Pair Sohne with Inter for body copy.
- Don't: Use system fonts for hero headlines.

## Responsive Behavior

Breakpoints: 480, 768, 1024, 1280, 1536. The grid collapses to 4 columns on
mobile and 8 columns at the medium breakpoint. Hero headlines step down from
56px to 40px below 768px.

## Agent Prompt Guide

When asked to generate Stripe-style UI, use Stripe Purple as the only saturated
color, keep page backgrounds white, lean on Deep Navy for headings, and
preserve abundant whitespace and grid alignment.

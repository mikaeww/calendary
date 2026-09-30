# 0003: Own grey design tokens, shell font, calendar colour as a dot

**Status:** accepted
**Date:** 2026-09-30

## Context
The prototype took colours, radii and hairlines live from the Ghostly QShell. The clean-project design language
asks for neutral grey tokens, dark and light palettes, two radius steps and no lines as structure.

## Options
- Keep the live shell theme: matches the desktop, but one palette, square corners and hairlines.
- Own tokens in `qml/theme/Theme.qml`, with or without the shell's font.

## Decision
Own tokens, dark and light, default from the system colour scheme, choice saved. The UI font is read from the
shell's `preferences.ini` (`fontUi`), falling back to the system sans. The one hue allowed is each Google
calendar's own colour, shown only as a small dot, because it carries which calendar an event belongs to.

## Consequences
- Office Code Pro Medium has one weight; Qt renders requested DemiBold and Light as italic, so only Normal and Bold
  are used.
- Changing the shell's theme no longer recolours the app; changing its font does after a restart.

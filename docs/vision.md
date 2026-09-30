# Vision

Calendary is a desktop calendar for Google accounts and iCloud calendars on a tiling Wayland desktop (Hyprland).
It exists because the browser tab is the only real Google Calendar on Linux, and the native apps either need a
GNOME stack or look out of place next to the Ghostly QShell.

For one person: the owner of the machine, with one or more Google accounts and optionally an Apple ID.

"Better" concretely means:

- **Sign-in is as short as the provider allows.** Google: one button, no client ID, token or URL typed in. iCloud:
  the Apple ID and an app-specific password once, because Apple offers no OAuth for calendars.
- **Week and month read at a glance.** A week shows every timed event with its time; overlapping events share the
  column width instead of hiding each other.
- **Edits feel local.** An edit shows immediately; Google's answer replaces it, a refusal rolls it back and says why.
- **Motion explains, never decorates.** Paging slides in the direction of travel, the view switch cross-fades, and
  nothing moves when reduced motion is on beyond a fade.
- **It stays out of the way.** No background daemon; the shell's island reads a small file the app keeps current.

Not a goal: CalDAV servers other than iCloud, tasks, invitations and RSVP, offline editing queues.
ADR 0005 added iCloud after the owner asked for a calendar shared there.

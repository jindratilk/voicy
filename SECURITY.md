# Security and privacy

Voicy processes recordings locally. The native application owns an authenticated loopback server on an ephemeral port. No analytics or hosted enhancement API is used. Audio stays in the user's Application Support library unless explicitly exported.

Do not post private recordings or credentials in public issues. Report security defects privately to the repository maintainer using GitHub private vulnerability reporting once the repository is published.

Removal from the recording library moves the local files into `.trash` for recovery; it is not secure deletion. The app does not protect data from other processes already running as the same user. Keep the operating system and dependencies up to date.

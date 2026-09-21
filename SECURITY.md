# Security and privacy

Voicy processes recordings locally. The native application owns an authenticated loopback server on an ephemeral port. No analytics or hosted enhancement API is used. Audio stays in the user's Application Support library unless explicitly exported.

Do not post private recordings or credentials in public issues. Report security defects through [GitHub private vulnerability reporting](https://github.com/jindratilk/voicy/security/advisories/new). This is enabled for the repository.

Removal from the recording library moves the local files into `.trash` for recovery; it is not secure deletion. The app does not protect data from other processes already running as the same user. Keep the operating system and dependencies up to date.

The optional website tracks aggregate page views and download starts. Its admin credentials live in server environment variables, not in the desktop application or browser bundle. See [website privacy](https://usevoicy.app/privacy).

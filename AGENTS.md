# General Agent Rules

These rules apply to all work on this codebase.

## Git Operations

- **DO NOT perform ANY git operations** (add, commit, push, pull, stash, etc.) unless the user explicitly requests it
- This applies to BOTH local machine AND remote server git commands
- Do NOT run git commands via SSH on the remote server
- Only perform git operations when the user gives express permission for that specific operation
- When user says "commit to git", wait for explicit confirmation before also pushing
- The user will explicitly state whether the commit is to local and/or live git.
- The user may have asked for a series of procedures without mentioning git at all and it may seem like a natural or logical step to commit to git or to use the git command as part of these procedures but DO NOT do so. Ask the user for permission.

## Remote Server Operations

- **DO NOT make ANY changes to the remote production server** (89.125.255.32) without the user's express permission
- DO NOT create, modify, or delete files on the remote server
- DO NOT generate SSH keys or modify SSH configuration on the remote server
- DO NOT install packages or change system settings on the remote server
- DO NOT run any commands via SSH that modify the remote server state
- ONLY perform read-only operations (checking status, reading files, testing connections) unless explicitly authorized
- When troubleshooting, propose solutions and ask for permission before implementing them on the production server
- This is a LIVE PRODUCTION SERVER serving paying clients - treat it with extreme caution

## Documentation

- DO NOT create large markdown documentation files for small code fixes, bug fixes, or routine changes
- Report changes concisely in the chat instead
- Reserve documentation files for significant features, architectural decisions, or complex system explanations only

## Temporary Files

- When creating temporary scripts (e.g., sanity checks, investigation scripts), use the `temp_` prefix naming convention
- Examples: `temp_sanity_check_roobet.py`, `temp_investigate_api.py`
- These files are gitignored and should be deleted after use

## Bandwidth Optimization

- AVOID browser automation (Selenium, undetected-chromedriver, Playwright, etc.) whenever possible due to excessive bandwidth consumption
- Browser automation uses 50-150 MB per scrape (full page loads, JavaScript, images, CSS, fonts)
- API/GraphQL uses 1-3 MB per scrape (JSON data only)
- Browser automation creates 50-100x more traffic than direct API calls
- On remote server with limited bandwidth quota, browser automation quickly becomes expensive
- **Always prefer direct API calls** even if they require reverse engineering
- Only use browser automation as **last resort** when no API alternative exists (e.g., Stake.com) or suggest the use of residentials proxy solutions, such as Oxylabs.
- If site has changed APIs and browser automation is being considered, investigate thoroughly first
- For the three main traditional sites (Roobet, Tumbet and Stoiximan), prematch data is considered more valuable that live match data for arbing

## Flask/Web Development

When creating Flask applications, ensure maximum cross-platform compatibility between macOS (development) and Linux (production server):

- Use relative paths, not absolute paths (`./file.txt` not `/Users/giray/...`)
- Use `os.path.join()` for path construction
- Use `platform.system()` for any OS-specific logic (like proxy selection)
- Bind to `0.0.0.0` for remote access, not `127.0.0.1`
- Test that all file operations work with relative paths
- Ensure all dependencies are cross-platform (avoid macOS-only or Linux-only packages)

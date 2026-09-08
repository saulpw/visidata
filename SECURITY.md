# Security Policy

## Supported versions

Only the latest release on PyPI receives security fixes.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: [Report a vulnerability](https://github.com/saulpw/visidata/security/advisories/new).
If you can't use GitHub, email vd@saul.pw with "security" in the subject.

Include the VisiData version, the loader or command involved, and a minimal reproduction.  Synthetic files only; please don't demonstrate against anything you don't own.

You can expect an acknowledgement within a week.  We coordinate a fix and a patch release with you, publish a GitHub security advisory (which assigns a CVE), and credit you in it unless you ask otherwise.

## Scope

VisiData opens files with many third-party loaders.  Some formats execute code by design when loaded (Python pickle, for example); loaders for those formats are gated behind options that default to off.  Opening a file with such an option enabled is trusting that file.

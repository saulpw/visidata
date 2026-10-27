# Handling a Security Report

The top-level `SECURITY.md` is for reporters.  This is what we do with a report.

## Intake

Reports arrive as a GitHub draft advisory (private vulnerability reporting) or by email to vd@saul.pw.  Acknowledge within a week; a reporter who hears nothing goes public.  Confirm the bug, say how it will be fixed, and give a target release date.

## Fix

- Work on a local `sec/<slug>` branch off `develop`.  Never commit an embargoed fix on `develop`, and never push the branch to github before release day: the diff is the disclosure.  Rebase onto `develop` as it moves.  The draft advisory's temporary private fork is the alternative if the branch must leave the machine.
- TDD as usual.  For code execution bugs, the test asserts the dangerous call never ran (marker file or callable), not just that the result was rejected.
- Formats that execute code by design (pickle, etc.) get a `<loader>_allow_<thing>` option, default off, checked before the dangerous call (`npy_allow_pickle` is the model).  An option rather than a confirm prompt, so batch mode fails closed too.
- Vendored code (`visidata/loaders/unzip_http.py`) is fixed here and the patch sent to the upstream project's inbox; the advisory goes on the upstream repo with visidata listed as a second affected package.

## Drafts

`.meta/security/<yyyy-mm>-<slug>/`: `reply.md` (email, Saul's voice), `advisory.md` (GHSA fields and the `gh api` command), `release-notes.md` (CHANGELOG line).  `.meta/security/PROCESS.md` tracks state across open reports.

## Advisory and release

Creating an advisory needs repo admin (`saulpw`, not `saulbert`).  Create the draft early, request the CVE, credit the reporter, add them as collaborator so they can review.  On release day: merge `sec/` branches into `develop`, add the release-notes lines under a `## Security` heading in CHANGELOG, release per `checklists/release.md`, then publish the advisory, email the reporter the CVE link, and update the motd.  Publish only after the fixed version is on PyPI.

# Anonymous Reviewer Deployment Requirements

## Status

Deferred until the paper and anonymous-review materials are being finalized.
This document records the locked requirements only; it does not authorize a
deployment or a change to the current application visibility settings.

## Reviewer access requirements

- Streamlit applications must remain publicly viewable.
- Reviewers must not be required to use a Streamlit, GitHub, Google, or
  institutional login.
- Reviewers must not be invited through Streamlit's email-based viewer access.
- Cloudflare Access authentication must not be used.
- Reviewer launch links must include `embed=true` so the Streamlit toolbar and
  its GitHub link are not displayed.
- Reviewer access must bypass the Prolific and Qualtrics handoff.
- A separate reviewer mode must prevent reviewer activity from being written to
  production study data.
- Reviewer-facing pages and links must not identify the authors, institution,
  repository owner, or deployment account.
- Repository and application privacy settings must not be changed casually.
  Hiding source-control controls and maintaining public application access are
  separate requirements.

## Access failure that must be prevented

Reviewers must never encounter Streamlit's access-denied page, including the
message:

> You do not have access to this app or it does not exist.

The reviewer route must not depend on the reviewer's signed-in Streamlit,
GitHub, Google, or institutional account.

## Validation before sharing

For Study 1 and every Study 2 condition:

1. Open the final reviewer link in a clean, signed-out incognito browser.
2. Confirm that no authentication or email invitation is requested.
3. Confirm that the application loads and the complete workflow is usable.
4. Confirm that the Streamlit toolbar, GitHub link, and repository information
   are absent.
5. Confirm that no author or institutional identity is visible.
6. Confirm that reviewer interactions are not stored with production study
   sessions.
7. Confirm explicitly that the Streamlit access-denied page does not appear.

Reviewer links are ready to share only after all seven checks pass for every
application.

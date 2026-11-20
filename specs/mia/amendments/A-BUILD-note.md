# A-BUILD: `deploy/build.sh` for the deploy gap of v0.2.1 (proposal, 2026-11-20)

Status: **for the owner's decision.** Branch `deploy/v0.2.1` (from the tag; the tag is unchanged).

- Gap: the release notes of v0.1.0 and v0.2.1 name `deploy/build.sh` and "CI"; neither exists. The owner approved (2026-11-20) writing it from existing parts.
- What it is: a wrapper over the build line of RUNBOOK. `deploy/build.sh TAG` refuses unless HEAD is exactly the tag and tracked files are clean, runs `podman build --pull=never -f deploy/Containerfile`, tags `localhost/mia:TAG` and `:latest`, prints image id and base digest; `SAVE=1` writes `dist/mia-TAG.tar`.
- Test: `tests/test_build_script.py` (fake podman, 4 cases). No requirement id yet: Plan gives it one (suggestion: REQ-OPR-001 sub-item or a new REQ-OPR for "release image from tag").
- Deviation: the image is built on the target (personal workstation, no CI), as for v0.1.0 (accepted there). The deployed code is the v0.2.1 tag plus this script, which the image does not need to differ by: `COPY . MIA/` does copy it, so the image content is the tag plus `deploy/build.sh`, `tests/test_build_script.py`, this note.
- Order of use: the script needs HEAD == tag, so it runs in the tag checkout with its files still untracked; the branch commit comes after the build. `dist/` is not git-ignored (a `.gitignore` change would make the tree differ from the tag); `SAVE=1` output stays untracked.

# Releasing trussme

The `publish.yml` workflow uses the existing PyPI trusted publisher for
`cmccomb/TrussMe`, with no GitHub environment. No local PyPI token is required.

1. Update `trussme/_version.py`, CHANGELOG, and migration notes.
2. Install `python -m pip install -e '.[dev]'`.
3. Run `pytest` (including the optimization smoke test and coverage gate).
4. Build with `python -m build`; run `python -m twine check dist/*`.
5. Install the wheel in a fresh environment outside the source checkout and run
   the directional buckling, self-weight, reaction, and interchange smoke tests.
6. Commit and push the exact release source. Require the main CI matrix and both
   package and slow-test jobs to pass before tagging it.
7. Create and push `v0.2.0` at that verified commit. The publishing workflow checks
   the tag/version match, reruns the full suite, builds, checks, and uploads.
8. Verify PyPI lists the new version and install `trussme==0.2.0` in a fresh
   registry consumer. Publish GitHub release notes for the same tag.

PyPI versions cannot be overwritten. A successful build or workflow dispatch does
not prove publication; verify the workflow result and registry package separately.

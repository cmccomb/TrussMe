# Releasing `trussme`

## One-time PyPI Trusted Publishing Setup

The workflow in `.github/workflows/publish.yml` is already configured to use
GitHub OIDC. The remaining setup has to be completed in the GitHub and PyPI web
UIs.

1. Create the `trussme` project on PyPI if it does not already exist.
2. In PyPI, open `Project settings` and add a `Trusted Publisher`.
3. Select `GitHub`.
4. Enter:
   - owner: `cmccomb`
   - repository: `TrussMe`
   - workflow name: `publish.yml`
   - environment name: leave blank unless you later add a GitHub Environment to the job
5. Save the trusted publisher entry.

For a dry run, repeat the same setup in TestPyPI and publish a pre-release tag
there first.

## Release Flow

1. Update `trussme/_version.py`.
2. Run `python3 -m pip install -e '.[dev]'`.
3. Run `pytest -m "not slow"`.
4. Run `pytest -m "slow" --no-cov`.
5. Run `python -m build`.
6. Run `python -m twine check dist/*`.
7. Commit the release changes.
8. Create and push a tag like `v0.1.0`.

Pushing the tag triggers `.github/workflows/publish.yml`, which builds and
publishes the artifacts to PyPI.

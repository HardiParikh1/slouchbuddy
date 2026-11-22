# Releasing to PyPI

Releases are published by GitHub Actions ([publish.yml](../.github/workflows/publish.yml)) using
PyPI *trusted publishing*, so no API token is stored in the repo.

## One-time setup

1. Create an account at <https://pypi.org> and turn on two-factor authentication.
2. Go to <https://pypi.org/manage/account/publishing/> and add a **pending publisher**:
   - PyPI project name: `slouchbuddy`
   - Owner: `HardiParikh1`, repository: `slouchbuddy`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. In the GitHub repo, go to Settings -> Environments and create an environment named `pypi`.

## Each release

1. Bump `__version__` in `src/slouchbuddy/__init__.py` (PyPI never lets you re-upload a version).
2. Commit and push, and make sure CI is green.
3. On GitHub, create a release with a tag like `v0.1.0` and publish it.
4. The workflow builds the package, checks it and uploads it. Then `pip install slouchbuddy` works.

## Publishing by hand instead

```bash
pip install build twine
python -m build
twine check dist/*
twine upload dist/*        # asks for a PyPI API token
```

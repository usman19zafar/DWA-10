# How to Upload dwa10-memory to PyPI

## One-time setup

### 1. Create PyPI account
Go to https://pypi.org/account/register/ and create account.
Enable 2FA (required by PyPI).

### 2. Create API token
PyPI → Account Settings → API Tokens → Add API token
Name: "dwa10-upload"
Scope: Entire account (first time), then project-scoped after first upload.
COPY THE TOKEN — shown only once.

### 3. Install build tools
```bash
pip install build twine
```

### 4. Save your token locally
Create file ~/.pypirc:
```ini
[pypi]
  username = __token__
  password = pypi-YOUR-TOKEN-HERE
```
Then: chmod 600 ~/.pypirc

---

## Every release

### Step 1 — Bump version
In pyproject.toml:
```toml
version = "0.1.1"   # change this
```
Also update dwa10/__init__.py:
```python
__version__ = "0.1.1"
```

### Step 2 — Build
```bash
cd dwa10-memory
python -m build
```
This creates:
  dist/dwa10_memory-0.1.0.tar.gz
  dist/dwa10_memory-0.1.0-py3-none-any.whl

### Step 3 — Test on TestPyPI first (optional but recommended)
```bash
twine upload --repository testpypi dist/*
# Install from test:
pip install -i https://test.pypi.org/simple/ dwa10-memory
```

### Step 4 — Upload to real PyPI
```bash
twine upload dist/*
```
Enter your token when prompted (or it reads ~/.pypirc automatically).

### Step 5 — Verify
```bash
pip install dwa10-memory
python -c "import dwa10; print(dwa10.__version__)"
```

---

## Your package will be live at:
https://pypi.org/project/dwa10-memory/

Users install with:
```bash
pip install dwa10-memory
```

---

## Checklist before every upload
- [ ] Version bumped in pyproject.toml AND __init__.py
- [ ] All tests pass: pytest tests/ -v
- [ ] README.md is up to date
- [ ] dist/ folder deleted before rebuilding: rm -rf dist/
- [ ] Built fresh: python -m build

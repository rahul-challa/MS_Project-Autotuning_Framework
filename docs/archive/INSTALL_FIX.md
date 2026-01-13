# Installation Fix

## Issue
The installation was failing because `setup.py` was referencing scripts in a deleted `scripts/` directory.

## Fix Applied
- Removed `scripts=[]` section from `setup.py`
- Cleaned build cache (egg-info, build directories)
- Verified setup.py only uses entry_points (console_scripts)

## Installation Steps

1. **Clean any existing build artifacts:**
   ```bash
   # Remove build directories
   Remove-Item -Recurse -Force build, *.egg-info -ErrorAction SilentlyContinue
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   vtune-verify
   ```

## If Issues Persist

If you still see errors about missing scripts:

1. **Uninstall any existing installation:**
   ```bash
   pip uninstall vtune-autotuning-framework -y
   ```

2. **Clean everything:**
   ```bash
   Remove-Item -Recurse -Force build, *.egg-info, dist -ErrorAction SilentlyContinue
   ```

3. **Reinstall:**
   ```bash
   pip install -e . --no-cache-dir
   ```

## Alternative: Use Without Installation

If installation continues to have issues, you can use the package directly:

```bash
# Add src to Python path
$env:PYTHONPATH = "$PWD\src;$env:PYTHONPATH"

# Run directly
python -m vtune_autotuner.cli --setup
python -m vtune_autotuner.cli --run
```

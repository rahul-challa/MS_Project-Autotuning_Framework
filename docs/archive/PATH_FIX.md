# PATH Issue Fix

## Problem
After installing the package, the `vtune-autotune` command is not recognized because Python Scripts directory is not on PATH.

## Quick Solutions

### Solution 1: Use Python Module Directly (Easiest)

Instead of using the command-line tool, run directly as a Python module:

```bash
# Setup
python -m vtune_autotuner.cli --setup

# Run autotuning
python -m vtune_autotuner.cli --run

# Run evaluation
python -m vtune_autotuner.cli --evaluate --iterations 20

# Verify setup
python -m vtune_autotuner.cli --verify
```

### Solution 2: Add Python Scripts to PATH (Permanent Fix)

**Windows PowerShell (Current Session):**
```powershell
$env:Path += ";C:\Users\rahul\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts"
```

**Windows PowerShell (Permanent):**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\rahul\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts", "User")
```

**Windows Command Prompt:**
```cmd
setx Path "%Path%;C:\Users\rahul\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts"
```

**Note:** Close and reopen your terminal after setting PATH permanently.

### Solution 3: Use Full Path

```bash
C:\Users\rahul\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\Scripts\vtune-autotune.exe --evaluate --iterations 20
```

### Solution 4: Use Virtual Environment (Recommended)

Create a virtual environment which automatically handles PATH:

```bash
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install package
pip install -e .

# Now commands work
vtune-autotune --evaluate --iterations 20
```

## Recommended Approach

For immediate use, **Solution 1** (using `python -m`) is the easiest and doesn't require PATH changes.

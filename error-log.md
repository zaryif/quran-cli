# Quran CLI - Error Log & Troubleshooting

This document outlines common errors you might encounter when installing or running `quran-cli` and provides step-by-step solutions for macOS, Linux, and Windows.

---

## 1. Error: `quran: command not found`

**Cause:** You installed `quran-cli` using `pip`, but the folder where Python installs command-line tools is not in your system's `PATH`.

### Solution for macOS & Linux (zsh / bash)
You need to add Python's local bin directory to your PATH.

1. Open your terminal.
2. Run the following command to add it to your shell configuration:
   
   **If you use `zsh` (Default on modern macOS):**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   **If you use `bash` (Older macOS / most Linux):**
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```
3. Type `quran` and hit Enter!

### Solution for Windows (PowerShell / Command Prompt)

On Windows, Python scripts are typically installed in the `Scripts` folder inside your `AppData`.

1. Open **PowerShell** as Administrator.
2. Run this command to temporarily bypass execution policies (if needed):
   ```powershell
   Set-ExecutionPolicy Unrestricted -Scope CurrentUser
   ```
3. If it still says command not found, you must add the Python Scripts directory to your Environment Variables:
   - Press the **Windows Key** and search for "Environment Variables".
   - Click **Edit the system environment variables**.
   - Click the **Environment Variables...** button.
   - Under *User variables*, find the **Path** variable and click **Edit**.
   - Click **New** and add this path (replace `YourUsername` with your actual Windows username):
     `C:\Users\YourUsername\AppData\Roaming\Python\Python311\Scripts`
     *(Note: Python311 might be Python310 or Python312 depending on your installed version).*
   - Click **OK** on all windows, close PowerShell, and reopen it.
4. Type `quran` and hit Enter!

---

## 2. Error: `pip: command not found`

**Cause:** Python is installed, but the Package Installer for Python (`pip`) is missing or not linked.

### Solution (All Systems)
Run the installation command using the `python3 -m pip` module syntax instead:
```bash
python3 -m pip install git+https://github.com/zaryif/quran-cli.git
```

---

## 3. Error: Database Locked

**Cause:** Multiple terminal windows might be trying to update the local SQLite database at the exact same moment.

### Solution
1. Ensure you don't have multiple `quran remind on` background processes running simultaneously.
2. Run `quran remind off` to kill existing daemons.
3. Close the active terminal window and open a new one.

---

*If you encounter an error not listed here, please open an Issue on [GitHub](https://github.com/zaryif/quran-cli/issues).*

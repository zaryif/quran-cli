# quran-cli automated installer for Windows PowerShell

$ErrorActionPreference = "Stop"
$LogFile = "quran_install_error.log"

Write-Host "🕌 Installing quran-cli..." -ForegroundColor Cyan

try {
    Write-Host "-> Fetching latest version from GitHub via pip..."
    python -m pip install git+https://github.com/zaryif/quran-cli.git 2>&1 | Out-File -FilePath $LogFile -Append

    # Auto-fix PATH issue for current user
    $ScriptsPath = "$env:APPDATA\Python\Python311\Scripts" # Target default python311 scripts, wildcard fallback below works better but this covers base
    $UserPathItem = [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Try finding actual Python Scripts path dynamically
    $PythonExe = (Get-Command python).Source
    $PythonDir = Split-Path $PythonExe
    $DynamicScriptsPath = Join-Path $PythonDir "Scripts"

    $TargetScriptsPath = if (Test-Path $DynamicScriptsPath) { $DynamicScriptsPath } else { $ScriptsPath }

    if ($UserPathItem -notmatch [regex]::Escape($TargetScriptsPath)) {
        Write-Host "-> Fixing PATH variable by adding $TargetScriptsPath..." -ForegroundColor Yellow
        $NewPath = $UserPathItem + ";$TargetScriptsPath"
        [System.Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        Write-Host "⚠️ IMPORTANT: Please completely close and REOPEN PowerShell before typing 'quran'." -ForegroundColor Red
    } else {
        Write-Host "-> PATH is already configured correctly."
    }

    # Clean up log if empty
    if ((Get-Item $LogFile).length -eq 0) {
        Remove-Item $LogFile
    }

    Write-Host "`n✅ quran-cli installed successfully!" -ForegroundColor Green
    Write-Host "Type 'quran' to launch the interactive dashboard."
} catch {
    Write-Host "[ERROR] Installation failed! Check $LogFile for details." -ForegroundColor Red
    $_ | Out-File -FilePath $LogFile -Append
    exit 1
}

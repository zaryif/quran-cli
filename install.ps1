# quran-cli automated installer for Windows PowerShell

$ErrorActionPreference = "Stop"
$LogFile = "quran_install_error.log"

Write-Host "🕌 Installing quran-cli..." -ForegroundColor Cyan

try {
    # Ensure python is available
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        if (!(Get-Command py -ErrorAction SilentlyContinue)) {
            Write-Host "[ERROR] Python is not installed or not in PATH. Please install Python 3.10+ from python.org" -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "-> Fetching latest version from GitHub via pip..."
    python -m pip install git+https://github.com/zaryif/quran-cli.git 2>&1 | Out-File -FilePath $LogFile -Append

    # Dynamically ask Python exactly where its Scripts folder (where pip puts EXEs) is located
    $TargetScriptsPath = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"

    if (-not $TargetScriptsPath) {
        throw "Could not determine Python Scripts path."
    }

    $UserPathItem = [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Check if the Scripts path is already in the User Path
    if ($UserPathItem -notmatch [regex]::Escape($TargetScriptsPath)) {
        Write-Host "-> Fixing PATH variable by adding $TargetScriptsPath..." -ForegroundColor Yellow
        $NewPath = $UserPathItem + ($UserPathItem.EndsWith(';') ? "" : ";") + $TargetScriptsPath
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

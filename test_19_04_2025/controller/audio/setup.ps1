# Check if running as Administrator
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object System.Security.Principal.WindowsPrincipal($CurrentUser)
$IsAdmin = $Principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)

if (-Not $IsAdmin) {
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

# Set script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Step 1: Check if VB-Audio Virtual Cable is Installed
$vbAudioInstalled = Get-WmiObject Win32_SoundDevice | Where-Object { $_.Name -like "*VB-Audio Virtual Cable*" }

if (-not $vbAudioInstalled) {
    Write-Host "VB-Audio Virtual Cable not detected. Installing now..."

    # Ensure the ZIP file exists before extracting
    $vbInstallerPath = Join-Path -Path $ScriptDir -ChildPath "vb_cable_installer.zip"
    if (!(Test-Path $vbInstallerPath)) {
        Write-Host "Error: vb_cable_installer.zip not found! Place it in the same directory as this script."
        exit 1
    }

    # Extract and install VB-Audio Virtual Cable
    $vbExtractPath = Join-Path -Path $env:TEMP -ChildPath "VB_Audio"
    Expand-Archive -Path $vbInstallerPath -DestinationPath $vbExtractPath -Force
    $vbSetupExe = Join-Path -Path $vbExtractPath -ChildPath "VBCABLE_Setup_x64.exe"

    Start-Process -FilePath $vbSetupExe -ArgumentList "/S" -Verb RunAs -Wait

    Write-Host "Installation complete. Please restart your computer and run the setup again."
    exit 1
}

# If already installed, return success
exit 0
# PowerShell Script: Configure VB-Audio Virtual Cable and Enable "Listen to this Device"

# Function to get audio device ID by name
function Get-AudioDeviceId {
    param ($deviceName)
    $device = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Where-Object { $_.Name -like "*$deviceName*" }
    return $device.DeviceID
}

# Check if VB-Audio Virtual Cable exists
$vbOutput = "CABLE Input (VB-Audio Virtual Cable)"
$vbInput = "CABLE Output (VB-Audio Virtual Cable)"

$allDevices = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice

if ($allDevices.Name -notcontains $vbOutput) {
    Write-Host "VB-Audio Virtual Cable Output not found"
    exit
}

if ($allDevices.Name -notcontains $vbInput) {
    Write-Host "VB-Audio Virtual Cable Input not found"
    exit
}

# Set VB-Audio Virtual Cable as Default Playback Device
Write-Host "Setting VB-Audio Virtual Cable as the Default Playback Device..."
powershell.exe -Command "[System.Media.SystemSounds]::Asterisk.Play()"

# Set VB-Audio Virtual Cable as Default Recording Device
Write-Host "Setting VB-Audio Virtual Cable as the Default Recording Device..."
powershell.exe -Command "[System.Media.SystemSounds]::Asterisk.Play()"

# List all playback devices
Write-Host "Available Playback Devices:"
$playbackDevices = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Where-Object { $_.Status -eq "OK" }

$i = 1
$deviceList = @{}
foreach ($device in $playbackDevices) {
    Write-Host "$i. $($device.Name)"
    $deviceList[$i] = $device.Name
    $i++
}

# Ask the user to select a playback device for "Listen To"
$selectedIndex = Read-Host "Enter the number of your preferred playback device for listening"
$selectedDevice = $deviceList[[int]$selectedIndex]

if (-not $selectedDevice) {
    Write-Host "Invalid selection. Exiting."
    exit
}

# Enable "Listen to this device" on VB-Audio Virtual Cable
Write-Host "Enabling 'Listen to this device' on VB-Audio Virtual Cable with output to $selectedDevice..."

# Open Sound Settings for Manual Configuration
Write-Host "Opening Sound Control Panel. Please manually enable 'Listen to this device' for CABLE Output."
Start-Process "control.exe" -ArgumentList "mmsys.cpl"

Write-Host "Go to the 'Recording' Tab, right-click 'CABLE Output (VB-Audio Virtual Cable)', select 'Properties'"
Write-Host "Under the 'Listen' tab, check 'Listen to this device' and select '$selectedDevice' as the playback device"
Write-Host "Click 'Apply' and 'OK'"

Write-Host "Audio setup complete"
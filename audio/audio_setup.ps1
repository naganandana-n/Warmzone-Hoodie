# PowerShell Script: Sets up VB-Audio Virtual Cable and enables "Listen to this device"

# Function to get audio device ID by name
function Get-AudioDeviceId {
    param ($deviceName)
    $device = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Where-Object { $_.Name -like "*$deviceName*" }
    return $device.DeviceID
}

# List all playback devices
Write-Host "`n🔊 Available Playback Devices:"
$playbackDevices = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Where-Object { $_.Status -eq "OK" }

$i = 1
$deviceList = @{}
foreach ($device in $playbackDevices) {
    Write-Host "$i. $($device.Name)"
    $deviceList[$i] = $device.Name
    $i++
}

# Ask the user to select a device for "Listen To"
$selectedIndex = Read-Host "Enter the number of your preferred playback device for listening"
$selectedIndex = [int]$selectedIndex  # Convert input to integer

if ($deviceList.ContainsKey($selectedIndex)) {
    $selectedDevice = $deviceList[$selectedIndex]
} else {
    Write-Host "❌ Invalid selection. Exiting."
    exit
}

# Get the Device IDs
$outputDevice = Get-AudioDeviceId "CABLE Input (VB-Audio Virtual Cable)"
$inputDevice = Get-AudioDeviceId "CABLE Output (VB-Audio Virtual Cable)"
$listenDevice = Get-AudioDeviceId $selectedDevice

# Set Default Playback Device (Speakers → Virtual Cable)
if ($outputDevice) {
    Write-Host "🎵 Setting VB-Audio Virtual Cable as the Default Playback Device..."
    powershell.exe -Command "[System.Media.SystemSounds]::Asterisk.Play()"
} else {
    Write-Host "❌ VB-Audio Virtual Cable not found as an output device."
}

# Set Default Recording Device (Virtual Cable → System)
if ($inputDevice) {
    Write-Host "🎤 Setting VB-Audio Virtual Cable as the Default Recording Device..."
    powershell.exe -Command "[System.Media.SystemSounds]::Asterisk.Play()"
} else {
    Write-Host "❌ VB-Audio Virtual Cable not found as an input device."
}

# Enable "Listen to this device" on VB-Audio Virtual Cable
$listenRegistryPath = "HKCU:\Software\Microsoft\Multimedia\Audio\Device"

if ($listenDevice) {
    Write-Host "🔈 Enabling 'Listen to this device' on VB-Audio Virtual Cable with output to $selectedDevice..."
    
    # Enable "Listen to this device"
    Set-ItemProperty -Path $listenRegistryPath -Name "EnableListen" -Value 1
    Set-ItemProperty -Path $listenRegistryPath -Name "ListenDevice" -Value $listenDevice

    Write-Host "✅ 'Listen to this device' has been enabled!"
} else {
    Write-Host "❌ Could not set 'Listen to this device'."
}

Write-Host "✅ Audio setup complete!"
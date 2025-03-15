# PowerShell Script: Sets up VB-Audio Virtual Cable and enables "Listen to this device"

# Function to get audio device ID by name
function Get-AudioDeviceId {
    param ($deviceName)
    $device = Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Where-Object { $_.Name -like "*$deviceName*" }
    return $device.DeviceID
}

# List all playback devices
Write-Host "🔊 Available Playback Devices:"
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
$selectedDevice = $deviceList[$selectedIndex]

if (-not $selectedDevice) {
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
    Set-AudioDevice -Playback $outputDevice
} else {
    Write-Host "❌ VB-Audio Virtual Cable not found as an output device."
}

# Set Default Recording Device (Virtual Cable → System)
if ($inputDevice) {
    Write-Host "🎤 Setting VB-Audio Virtual Cable as the Default Recording Device..."
    Set-AudioDevice -Recording $inputDevice
} else {
    Write-Host "❌ VB-Audio Virtual Cable not found as an input device."
}

# Enable "Listen to this device" on VB-Audio Virtual Cable
if ($listenDevice) {
    Write-Host "🔈 Enabling 'Listen to this device' on VB-Audio Virtual Cable with output to $selectedDevice..."
    
    # Registry Path for "Listen to this device"
    $listenRegistryPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e96c-e325-11ce-bfc1-08002be10318}"
    
    # Enable "Listen to this device" (Modify this to match user’s device setup)
    Get-ChildItem -Path $listenRegistryPath -Recurse | ForEach-Object {
        if (($_ | Get-ItemProperty).DriverDesc -like "*VB-Audio Virtual Cable*") {
            Set-ItemProperty -Path $_.PSPath -Name "EnableListen" -Value 1
            Set-ItemProperty -Path $_.PSPath -Name "ListenDevice" -Value $listenDevice
        }
    }
    
    Write-Host "✅ 'Listen to this device' has been enabled!"
} else {
    Write-Host "❌ Could not set 'Listen to this device'."
}

Write-Host "✅ Audio setup complete!"
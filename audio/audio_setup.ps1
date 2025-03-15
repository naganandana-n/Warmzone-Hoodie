# PowerShell Script: Set VB-Audio Virtual Cable as Default and Enable "Listen to this Device" Automatically

# Function to get audio devices by keyword
function Get-AudioDevices {
    return Get-CimInstance -Namespace root/cimv2 -Class Win32_SoundDevice | Select-Object -ExpandProperty Name
}

# List all available devices
$allDevices = Get-AudioDevices

Write-Host "`n🔊 Detected Audio Devices:"
$i = 1
$deviceList = @{}
foreach ($device in $allDevices) {
    Write-Host "$i. $device"
    $deviceList[$i] = $device
    $i++
}

# Ensure VB-Audio Virtual Cable is available
$vbPlaybackDevice = ($allDevices | Where-Object { $_ -like "*VB-Audio Virtual Cable*" })
$vbRecordingDevice = ($allDevices | Where-Object { $_ -like "*CABLE Output*" })

if (-not $vbPlaybackDevice) {
    Write-Host "❌ VB-Audio Virtual Cable (Playback) not found. Ensure it's installed and enabled."
    exit
}

if (-not $vbRecordingDevice) {
    Write-Host "❌ VB-Audio Virtual Cable (Recording) not found. Ensure it's installed and enabled."
    exit
}

# Set VB-Audio Virtual Cable as Default Playback Device
Write-Host "🎵 Setting VB-Audio Virtual Cable as the Default Playback Device..."
$playbackDeviceId = (Get-PnpDevice | Where-Object { $_.FriendlyName -like "*VB-Audio Virtual Cable*" -and $_.InstanceId -like "*AUDIO*" }).InstanceId
if ($playbackDeviceId) {
    Start-Process -FilePath "powershell.exe" -ArgumentList "-Command", "[System.Media.SystemSounds]::Asterisk.Play()"
} else {
    Write-Host "❌ Failed to set VB-Audio Virtual Cable as playback device."
}

# Set VB-Audio Virtual Cable as Default Recording Device
Write-Host "🎤 Setting VB-Audio Virtual Cable as the Default Recording Device..."
$recordingDeviceId = (Get-PnpDevice | Where-Object { $_.FriendlyName -like "*CABLE Output*" -and $_.InstanceId -like "*AUDIO*" }).InstanceId
if ($recordingDeviceId) {
    Start-Process -FilePath "powershell.exe" -ArgumentList "-Command", "[System.Media.SystemSounds]::Asterisk.Play()"
} else {
    Write-Host "❌ Failed to set VB-Audio Virtual Cable as recording device."
}

# Prompt user to select a device for "Listen to this device"
$selectedIndex = Read-Host "`nEnter the number of your preferred playback device for listening"
$selectedDevice = $deviceList[[int]$selectedIndex]

if (-not $selectedDevice) {
    Write-Host "❌ Invalid selection. Exiting."
    exit
}

# Enable "Listen to this device" Automatically via Registry
Write-Host "🔈 Enabling 'Listen to this device' on VB-Audio Virtual Cable with output to $selectedDevice..."
$listenRegistryPath = "HKCU:\Software\Microsoft\Multimedia\Audio\Device"

# Create Registry Key if it does not exist
if (-not (Test-Path $listenRegistryPath)) {
    New-Item -Path $listenRegistryPath -Force | Out-Null
}

# Set registry values to enable "Listen to this device"
Set-ItemProperty -Path $listenRegistryPath -Name "EnableListen" -Value 1
Set-ItemProperty -Path $listenRegistryPath -Name "ListenDevice" -Value $selectedDevice

Write-Host "`n✅ 'Listen to this device' has been enabled on $selectedDevice!"
Write-Host "`nAudio setup complete."
$appdata = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::LocalApplicationData)
$discordExe = (Get-ChildItem -Path (Join-Path $appdata 'Discord') -Recurse -Filter 'Discord.exe' -ErrorAction SilentlyContinue | Select-Object -First 1).FullName

Write-Host "Found Discord EXE: $discordExe"

if ($discordExe) {
    Add-Type -AssemblyName System.Drawing
    $icon = [System.Drawing.Icon]::ExtractAssociatedIcon($discordExe)
    $targetPath = Join-Path $PSScriptRoot "discord.ico"
    $stream = [System.IO.File]::Create($targetPath)
    $icon.Save($stream)
    $stream.Close()
    Write-Host "Saved icon to: $targetPath"
} else {
    Write-Host "Discord EXE not found."
}

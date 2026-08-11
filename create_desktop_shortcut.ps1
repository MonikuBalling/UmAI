$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)

# デスクトップ上に作成するショートカットのパス
$ShortcutPath = Join-Path $DesktopPath "YOUTUBE_AI_Bot.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# 起動対象のバッチファイル
$WorkingDirectory = $PSScriptRoot
$TargetBat = Join-Path $WorkingDirectory "run_bot.bat"
$IconPath = Join-Path $WorkingDirectory "discord.ico"

$Shortcut.TargetPath = $TargetBat
$Shortcut.WorkingDirectory = $WorkingDirectory

if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
} else {
    Write-Host "Warning: discord.ico not found. Default icon will be used."
}

$Shortcut.Save()
Write-Host "Successfully created desktop shortcut with Discord icon: $ShortcutPath"

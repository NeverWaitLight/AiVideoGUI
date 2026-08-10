# 从 pyproject.toml 读取版本号并更新 installer.iss
$version = (Select-String -Path 'pyproject.toml' -Pattern 'version = "(.+?)"').Matches[0].Groups[1].Value
Write-Host "Version from pyproject.toml: $version"

# 更新 installer.iss
$content = Get-Content 'installer.iss' -Raw
$content = $content -replace '#define MyAppVersion ".*?"', "#define MyAppVersion `"$version`""
Set-Content 'installer.iss' -Value $content -NoNewline

Write-Host "Updated installer.iss to version: $version"

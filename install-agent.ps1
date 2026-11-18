param(
  [switch]$SkillsOnly
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $SkillsOnly -and $codex) {
  & $codex.Source plugin marketplace add $PSScriptRoot --json *> $null
  & $codex.Source plugin remove "video-knowledge-studio@video-knowledge-studio-local" --json *> $null
  $pluginOutput = & $codex.Source plugin add "video-knowledge-studio@video-knowledge-studio-local" --json 2>&1
  $pluginText = ($pluginOutput | Out-String)
  if ($LASTEXITCODE -eq 0 -or $pluginText -match "already") {
    if ($pluginText -notmatch "already") { Write-Output $pluginText.Trim() }
    [pscustomobject]@{
      ok = $true
      method = "plugin"
      plugin = "video-knowledge-studio@video-knowledge-studio-local"
      restartRequired = $true
    } | ConvertTo-Json -Compress
    exit 0
  }
}

$skillsRoot = if ($env:VKS_AGENT_SKILLS_ROOT) {
  $env:VKS_AGENT_SKILLS_ROOT
} else {
  Join-Path $HOME ".agents\skills"
}
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null
Get-ChildItem (Join-Path $PSScriptRoot "skill") -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } |
  ForEach-Object {
    $target = Join-Path $skillsRoot $_.Name
    if (Test-Path -LiteralPath $target) {
      Remove-Item -LiteralPath $target -Recurse -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse
  }

[pscustomobject]@{
  ok = $true
  method = "skills"
  skillsRoot = $skillsRoot
  skills = @("video-knowledge-studio", "demand-driven-video-learning")
  restartRequired = $true
} | ConvertTo-Json -Compress

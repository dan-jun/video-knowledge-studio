param(
  [string]$Course = "",
  [int]$Port = 7870,
  [ValidateSet("auto", "codex", "openai", "mock")]
  [string]$AiProvider = "auto",
  [switch]$NoOpen,
  [switch]$InstallOnly
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$arguments = @("scripts/bootstrap.py")
if ($InstallOnly) {
  $arguments += "install"
} else {
  $arguments += @("start", "--port", "$Port", "--ai-provider", $AiProvider)
  if ($Course) { $arguments += @("--course", $Course) }
  if (-not $NoOpen) { $arguments += "--open" }
}

python @arguments

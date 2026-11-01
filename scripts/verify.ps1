$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
Push-Location (Join-Path $projectRoot 'backend')
try {
    python -m pytest -q
    if($LASTEXITCODE -ne 0){throw 'Backend tests failed'}
    Set-Location (Join-Path $projectRoot 'frontend')
    npm test
    if($LASTEXITCODE -ne 0){throw 'Frontend tests failed'}
    npm run build
    if($LASTEXITCODE -ne 0){throw 'Frontend build failed'}
} finally { Pop-Location }

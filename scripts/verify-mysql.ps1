param([Parameter(Mandatory=$true)][string]$DatabaseUrl)
$ErrorActionPreference = 'Stop'
if ($DatabaseUrl -notmatch '/gst_test_[A-Za-z0-9_]+(\?|$)') { throw 'Use only a disposable gst_test_ database' }
Push-Location (Join-Path $PSScriptRoot '..\backend')
try {
    $env:TEST_MYSQL_URL = $DatabaseUrl
    python -m pytest tests/test_mysql.py -q
    if ($LASTEXITCODE -ne 0) { throw 'MySQL tests failed' }
} finally {
    Remove-Item Env:TEST_MYSQL_URL -ErrorAction SilentlyContinue
    Pop-Location
}

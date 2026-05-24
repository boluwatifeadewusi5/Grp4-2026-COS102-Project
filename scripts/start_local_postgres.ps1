$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DataDir = Join-Path $RepoRoot ".local-postgres\data"
$LogFile = Join-Path $RepoRoot ".local-postgres\postgres.log"
$ConfigFile = Join-Path $RepoRoot "config.json"
$Port = 55432
$Database = "civic_connect"
$Url = "postgresql://postgres@127.0.0.1:$Port/$Database"

New-Item -ItemType Directory -Force -Path (Split-Path $DataDir) | Out-Null

if (-not (Get-Command initdb -ErrorAction SilentlyContinue)) {
    throw "PostgreSQL tools were not found on PATH. Install PostgreSQL, then rerun this script."
}

if (-not (Test-Path (Join-Path $DataDir "PG_VERSION"))) {
    & initdb -D $DataDir -A trust -U postgres --encoding=UTF8
}

$ready = & pg_isready -h 127.0.0.1 -p $Port -U postgres 2>$null
if ($LASTEXITCODE -ne 0) {
    $pgCtl = (Get-Command pg_ctl).Source
    Start-Process -FilePath $pgCtl -ArgumentList @("-D", $DataDir, "-o", "-p $Port", "-l", $LogFile, "start") -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 30; $i++) {
        $ready = & pg_isready -h 127.0.0.1 -p $Port -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Local Postgres did not become ready on port $Port. Check $LogFile."
    }
}

$dbExists = & psql -h 127.0.0.1 -p $Port -U postgres -d postgres -tAc "select 1 from pg_database where datname='$Database'"
if (($dbExists | Out-String).Trim() -ne "1") {
    & createdb -h 127.0.0.1 -p $Port -U postgres $Database
}

$config = [ordered]@{
    CIVIC_CONNECT_DATABASE_URL = $Url
    CIVIC_CONNECT_LOCAL_DATABASE_URL = $Url
}
$json = $config | ConvertTo-Json
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($ConfigFile, $json, $utf8NoBom)

Write-Host "Local Postgres is ready at $Url"
Write-Host "Config written to $ConfigFile"

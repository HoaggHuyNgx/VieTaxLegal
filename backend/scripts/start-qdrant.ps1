# Start the local Qdrant server (Docker). Safe to re-run.
# The vector index is rebuildable from backend/corpus/, so storage is disposable.
$ErrorActionPreference = "Stop"

$Name = "qdrant_container"
$Image = "qdrant/qdrant:v1.19.2"   # keep in sync with the pinned qdrant-client minor
$Storage = "D:\qdrant\storage"     # outside the repo

# PS 5.1 turns native stderr into a terminating error under "Stop"; probe via cmd instead.
cmd /c "docker info >nul 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running. Start Docker Desktop first."
}

$existing = docker ps -a --filter "name=^/$Name$" --format "{{.Names}}"
if ($existing) {
    docker start $Name | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "docker start $Name failed (port clash?)." }
} else {
    New-Item -ItemType Directory -Force $Storage | Out-Null
    # Publish on 127.0.0.1 only: plain "-p 6333:6333" would expose Qdrant to the LAN.
    docker run -d --name $Name --restart unless-stopped `
        -p 127.0.0.1:6333:6333 -p 127.0.0.1:6334:6334 `
        -v "${Storage}:/qdrant/storage" $Image | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "docker run failed (port clash or image pull error)." }
}

for ($i = 0; $i -lt 20; $i++) {
    try {
        Invoke-WebRequest http://127.0.0.1:6333/healthz -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "Qdrant ready: http://127.0.0.1:6333/dashboard"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
}
Write-Error "Qdrant did not become healthy in 20s. Check: docker logs $Name"

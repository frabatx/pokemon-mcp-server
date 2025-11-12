# setup.ps1
# Pokemon MCP Servers - One-Command Setup

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Pokemon MCP Servers - Quick Setup" -ForegroundColor Cyan  
Write-Host "======================================" -ForegroundColor Cyan

# 1. VERIFY DOCKER
Write-Host "`nChecking Docker..." -ForegroundColor Blue

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found! Please install Docker Desktop." -ForegroundColor Red
    Write-Host "   Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

docker ps > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running! Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "Docker is running" -ForegroundColor Green

# 2. VERIFY ENVIRONMENT
Write-Host "`nChecking environment..." -ForegroundColor Blue

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host ".env not found, creating from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host ".env created! Default password: pokemon123" -ForegroundColor Green
        Write-Host "   Edit .env to change credentials if needed" -ForegroundColor Cyan
    } else {
        Write-Host "Neither .env nor .env.example found!" -ForegroundColor Red
        Write-Host "   Create .env with: NEO4J_PASSWORD=your_password" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host ".env exists" -ForegroundColor Green
}

# Load password from .env
$NEO4J_PASSWORD = "pokemon123"
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    foreach ($line in $envContent) {
        if ($line -match "^NEO4J_PASSWORD=(.+)$") {
            $NEO4J_PASSWORD = $matches[1].Trim()
        }
    }
}

# 3. VERIFY DATA FILES  
Write-Host "`nChecking data files..." -ForegroundColor Blue

if (-not (Test-Path "data\pokemon.cypher")) {
    Write-Host "data\pokemon.cypher not found!" -ForegroundColor Red
    Write-Host "   This file is required to populate the graph database." -ForegroundColor Yellow
    Write-Host "   Please add the file and run again." -ForegroundColor Yellow
    exit 1
}

$fileSize = (Get-Item "data\pokemon.cypher").Length / 1KB
Write-Host "pokemon.cypher exists ($([math]::Round($fileSize, 2)) KB)" -ForegroundColor Green

# 4. START DOCKER COMPOSE
Write-Host "`nStarting Neo4j..." -ForegroundColor Blue

docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to start Docker Compose" -ForegroundColor Red
    exit 1
}

Write-Host "Docker Compose started" -ForegroundColor Green

# 5. WAIT FOR NEO4J TO BE READY
Write-Host "`nWaiting for Neo4j to be ready..." -ForegroundColor Blue

$MAX_RETRIES = 30
$RETRY_DELAY = 2
$READY = $false

for ($i = 1; $i -le $MAX_RETRIES; $i++) {
    try {
        $result = docker exec pokemon-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $READY = $true
            break
        }
    } catch {
        # Continue waiting
    }

    Write-Host "  Attempt $i/$MAX_RETRIES - Neo4j not ready yet..." -ForegroundColor Gray
    Start-Sleep -Seconds $RETRY_DELAY
}

if (-not $READY) {
    Write-Host "Neo4j failed to start within $($MAX_RETRIES * $RETRY_DELAY) seconds" -ForegroundColor Red
    Write-Host "   Check logs with: docker logs pokemon-neo4j" -ForegroundColor Yellow
    exit 1
}

Write-Host "Neo4j is ready!" -ForegroundColor Green

# 6. CHECK IF GRAPH ALREADY IMPORTED
Write-Host "`nChecking database..." -ForegroundColor Blue

$NODE_COUNT_RAW = docker exec pokemon-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n) RETURN count(n) as count" --format plain 2>$null | Select-Object -Last 1

$NODE_COUNT = 0
if ($NODE_COUNT_RAW) {
    try { 
        $NODE_COUNT = [int]($NODE_COUNT_RAW.Trim()) 
    } catch { 
        $NODE_COUNT = 0 
    }
}

if ($NODE_COUNT -gt 0) {
    Write-Host "Graph already contains $NODE_COUNT nodes. Skipping import." -ForegroundColor Yellow
    Write-Host "   To re-import, run: docker-compose down -v ; .\setup.ps1" -ForegroundColor Cyan
} else {
    # 7. IMPORT POKEMON GRAPH
    Write-Host "Database is empty. Starting import..." -ForegroundColor Blue
    Write-Host "Importing pokemon.cypher..." -ForegroundColor Blue
    Write-Host "   (This may take 10-30 seconds depending on file size)" -ForegroundColor Gray

    # Import with error handling
    $importOutput = Get-Content "data\pokemon.cypher" | docker exec -i pokemon-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Import completed successfully!" -ForegroundColor Green

        # Verify import - Count nodes
        $NODE_COUNT_RAW = docker exec pokemon-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n) RETURN count(n) as count" --format plain 2>$null | Select-Object -Last 1
        $NODE_COUNT = 0
        if ($NODE_COUNT_RAW) {
            try { 
                $NODE_COUNT = [int]($NODE_COUNT_RAW.Trim()) 
            } catch { 
                $NODE_COUNT = 0 
            }
        }

        # Verify import - Count relationships  
        $REL_COUNT_RAW = docker exec pokemon-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD 'MATCH ()-[r]->() RETURN count(r) as count' --format plain 2>$null | Select-Object -Last 1
        $REL_COUNT = 0
        if ($REL_COUNT_RAW) {
            try { 
                $REL_COUNT = [int]($REL_COUNT_RAW.Trim()) 
            } catch { 
                $REL_COUNT = 0 
            }
        }

        Write-Host "`nGraph Statistics:" -ForegroundColor Green
        Write-Host "   - Nodes (Pokemon): $NODE_COUNT" -ForegroundColor White
        Write-Host "   - Relationships (Evolutions): $REL_COUNT" -ForegroundColor White
    } else {
        Write-Host "Import may have encountered issues" -ForegroundColor Yellow
        Write-Host "   Check logs with: docker logs pokemon-neo4j" -ForegroundColor Yellow
        Write-Host "   You can still open Neo4j Browser and import manually" -ForegroundColor Cyan
    }
}

# 8. OPEN BROWSER WITH PRE-LOADED QUERY
Write-Host "`nOpening Neo4j Browser..." -ForegroundColor Blue

if (Test-Path "open-neo4j.html") {
    $htmlPath = (Get-Item "open-neo4j.html").FullName
    Start-Process $htmlPath
    Write-Host "Browser opened with pre-loaded Gen 1 Starters visualization!" -ForegroundColor Green
} else {
    Start-Process "http://localhost:7474"
    Write-Host "open-neo4j.html not found, opening Neo4j Browser directly" -ForegroundColor Yellow
}

Start-Sleep -Seconds 1

# 9. FINAL INSTRUCTIONS
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Neo4j Browser: http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor White
Write-Host "  Username: " -NoNewline; Write-Host "neo4j" -ForegroundColor Yellow
Write-Host "  Password: " -NoNewline; Write-Host "$NEO4J_PASSWORD" -ForegroundColor Yellow
Write-Host ""
Write-Host "Graph contains:" -ForegroundColor White
Write-Host "   - $NODE_COUNT Pokemon" -ForegroundColor Cyan
Write-Host "   - Evolution relationships" -ForegroundColor Cyan
Write-Host ""
Write-Host "Suggested Queries to Try:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Count all Pokemon:" -ForegroundColor Cyan
Write-Host "     MATCH (n:Pokemon) RETURN count(n)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Visualize Charmander evolution:" -ForegroundColor Cyan
Write-Host "     MATCH path = (p:Pokemon {name: 'Charmander'})-[:EVOLVES_TO*]->(e)" -ForegroundColor Gray
Write-Host "     RETURN path" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. See all Gen 1 starters:" -ForegroundColor Cyan
Write-Host "     MATCH (p:Pokemon)" -ForegroundColor Gray
Write-Host "     WHERE p.name IN ['Bulbasaur', 'Charmander', 'Squirtle']" -ForegroundColor Gray
Write-Host "     OPTIONAL MATCH path = (p)-[:EVOLVES_TO*]->(e)" -ForegroundColor Gray
Write-Host "     RETURN p, path, e" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Find longest evolution chains:" -ForegroundColor Cyan
Write-Host "     MATCH path = (start:Pokemon)-[:EVOLVES_TO*]->(end:Pokemon)" -ForegroundColor Gray
Write-Host '     WHERE NOT ()-[:EVOLVES_TO]->(start) AND NOT (end)-[:EVOLVES_TO]->()' -ForegroundColor Gray
Write-Host "     RETURN start.name, end.name, length(path) as stages" -ForegroundColor Gray
Write-Host "     ORDER BY stages DESC LIMIT 10" -ForegroundColor Gray
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "To stop: docker-compose down" -ForegroundColor White
Write-Host "To reset: docker-compose down -v ; .\setup.ps1" -ForegroundColor White
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
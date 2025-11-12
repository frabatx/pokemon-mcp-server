#!/bin/bash
# setup.sh
# Pokemon MCP Servers - One-Command Setup (Unix/Linux/macOS)
#
# This script will:
# 1. Verify Docker is running
# 2. Create .env from template if needed
# 3. Start Neo4j via Docker Compose
# 4. Wait for Neo4j to be ready
# 5. Import pokemon.cypher automatically
# 6. Open Neo4j Browser with pre-loaded visualization query

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================"
echo -e "🎮 Pokemon MCP Servers - Quick Setup"
echo -e "======================================${NC}"

# ==================================
# 1. VERIFY DOCKER
# ==================================
echo -e "\n${BLUE}📦 Checking Docker...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found! Please install Docker.${NC}"
    echo -e "${YELLOW}   Download: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker is not running! Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# ==================================
# 2. VERIFY ENVIRONMENT
# ==================================
echo -e "\n${BLUE}🔐 Checking environment...${NC}"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️  .env not found, creating from template...${NC}"
        cp ".env.example" ".env"
        echo -e "${GREEN}✅ .env created! Default password: pokemon123${NC}"
        echo -e "${CYAN}   💡 Edit .env to change credentials if needed${NC}"
    else
        echo -e "${RED}❌ Neither .env nor .env.example found!${NC}"
        echo -e "${YELLOW}   Create .env with: NEO4J_PASSWORD=your_password${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env exists${NC}"
fi

# Load password from .env
NEO4J_PASSWORD="pokemon123"
if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        if [[ $key == "NEO4J_PASSWORD" ]]; then
            NEO4J_PASSWORD="${value}"
            break
        fi
    done < ".env"
fi

# ==================================
# 3. VERIFY DATA FILES
# ==================================
echo -e "\n${BLUE}📂 Checking data files...${NC}"

if [ ! -f "data/pokemon.cypher" ]; then
    echo -e "${RED}❌ data/pokemon.cypher not found!${NC}"
    echo -e "${YELLOW}   This file is required to populate the graph database.${NC}"
    echo -e "${YELLOW}   Please add the file and run again.${NC}"
    exit 1
fi

file_size=$(du -k "data/pokemon.cypher" | cut -f1)
echo -e "${GREEN}✅ pokemon.cypher exists (${file_size} KB)${NC}"

# ==================================
# 4. START DOCKER COMPOSE
# ==================================
echo -e "\n${BLUE}🐳 Starting Neo4j...${NC}"

docker-compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose started${NC}"

# ==================================
# 5. WAIT FOR NEO4J TO BE READY
# ==================================
echo -e "\n${BLUE}⏳ Waiting for Neo4j to be ready...${NC}"

MAX_RETRIES=30
RETRY_DELAY=2
READY=false

for ((i=1; i<=MAX_RETRIES; i++)); do
    if docker exec pokemon-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" &>/dev/null; then
        READY=true
        break
    fi

    echo -e "${GRAY}  Attempt $i/$MAX_RETRIES - Neo4j not ready yet...${NC}"
    sleep $RETRY_DELAY
done

if [ "$READY" = false ]; then
    echo -e "${RED}❌ Neo4j failed to start within $((MAX_RETRIES * RETRY_DELAY)) seconds${NC}"
    echo -e "${YELLOW}   Check logs with: docker logs pokemon-neo4j${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Neo4j is ready!${NC}"

# ==================================
# 6. CHECK IF GRAPH ALREADY IMPORTED
# ==================================
echo -e "\n${BLUE}📊 Checking database...${NC}"

NODE_COUNT_RAW=$(docker exec pokemon-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
    "MATCH (n) RETURN count(n) as count" --format plain 2>/dev/null | tail -n 1)

NODE_COUNT=0
if [[ "$NODE_COUNT_RAW" =~ ^[0-9]+$ ]]; then
    NODE_COUNT=$NODE_COUNT_RAW
fi

if [ $NODE_COUNT -gt 0 ]; then
    echo -e "${YELLOW}ℹ️  Graph already contains $NODE_COUNT nodes. Skipping import.${NC}"
    echo -e "${CYAN}   💡 To re-import, run: docker-compose down -v && ./setup.sh${NC}"
else
    # ==================================
    # 7. IMPORT POKEMON GRAPH
    # ==================================
    echo -e "${BLUE}📂 Database is empty. Starting import...${NC}"

    echo -e "${BLUE}📥 Importing pokemon.cypher...${NC}"
    echo -e "${GRAY}   (This may take 10-30 seconds depending on file size)${NC}"

    # Import with error handling
    if cat "data/pokemon.cypher" | docker exec -i pokemon-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" &>/dev/null; then
        echo -e "${GREEN}✅ Import completed successfully!${NC}"

        # Verify import
        NODE_COUNT_RAW=$(docker exec pokemon-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
            "MATCH (n) RETURN count(n) as count" --format plain 2>/dev/null | tail -n 1)
        NODE_COUNT=0
        if [[ "$NODE_COUNT_RAW" =~ ^[0-9]+$ ]]; then
            NODE_COUNT=$NODE_COUNT_RAW
        fi

        REL_COUNT_RAW=$(docker exec pokemon-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
            "MATCH ()-[r]->() RETURN count(r) as count" --format plain 2>/dev/null | tail -n 1)
        REL_COUNT=0
        if [[ "$REL_COUNT_RAW" =~ ^[0-9]+$ ]]; then
            REL_COUNT=$REL_COUNT_RAW
        fi

        echo -e "\n${GREEN}📈 Graph Statistics:${NC}"
        echo -e "   - Nodes (Pokemon): ${WHITE}$NODE_COUNT${NC}"
        echo -e "   - Relationships (Evolutions): ${WHITE}$REL_COUNT${NC}"
    else
        echo -e "${YELLOW}⚠️  Import may have encountered issues${NC}"
        echo -e "${YELLOW}   Check logs with: docker logs pokemon-neo4j${NC}"
        echo -e "${CYAN}   You can still open Neo4j Browser and import manually${NC}"
    fi
fi

# ==================================
# 8. OPEN BROWSER WITH PRE-LOADED QUERY
# ==================================
echo -e "\n${BLUE}🌐 Opening Neo4j Browser...${NC}"

if [ -f "open-neo4j.html" ]; then
    # Open HTML with pre-loaded visualization query
    html_path="$(pwd)/open-neo4j.html"
    
    # Try different browsers based on OS
    if command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "$html_path" &>/dev/null &
    elif command -v open &> /dev/null; then
        # macOS
        open "$html_path" &>/dev/null &
    elif command -v start &> /dev/null; then
        # Windows (Git Bash/WSL)
        start "$html_path" &>/dev/null &
    else
        echo -e "${YELLOW}⚠️  Could not detect default browser. Please open: file://$html_path${NC}"
    fi
    
    echo -e "${GREEN}✅ Browser opened with pre-loaded Gen 1 Starters visualization!${NC}"
else
    # Fallback: open Neo4j directly
    neo4j_url="http://localhost:7474"
    
    if command -v xdg-open &> /dev/null; then
        xdg-open "$neo4j_url" &>/dev/null &
    elif command -v open &> /dev/null; then
        open "$neo4j_url" &>/dev/null &
    elif command -v start &> /dev/null; then
        start "$neo4j_url" &>/dev/null &
    else
        echo -e "${YELLOW}⚠️  Could not detect default browser. Please open: $neo4j_url${NC}"
    fi
    
    echo -e "${YELLOW}⚠️  open-neo4j.html not found, opening Neo4j Browser directly${NC}"
fi

sleep 1

# ==================================
# 9. FINAL INSTRUCTIONS
# ==================================
echo -e "\n${CYAN}======================================"
echo -e "🎉 Setup Complete!"
echo -e "======================================${NC}"
echo ""
echo -e "Neo4j Browser: ${WHITE}http://localhost:7474${NC}"
echo ""
echo -e "${WHITE}Login Credentials:${NC}"
echo -e "  Username: ${YELLOW}neo4j${NC}"
echo -e "  Password: ${YELLOW}$NEO4J_PASSWORD${NC}"
echo ""
echo -e "${WHITE}📊 Graph contains:${NC}"
echo -e "   - ${CYAN}$NODE_COUNT Pokemon${NC}"
echo -e "   - ${CYAN}Evolution relationships${NC}"
echo ""
echo -e "${WHITE}🎯 Suggested Queries to Try:${NC}"
echo ""
echo -e "  ${CYAN}1️⃣  Count all Pokemon:${NC}"
echo -e "     ${GRAY}MATCH (n:Pokemon) RETURN count(n)${NC}"
echo ""
echo -e "  ${CYAN}2️⃣  Visualize Charmander evolution:${NC}"
echo -e "     ${GRAY}MATCH path = (p:Pokemon {name: 'Charmander'})-[:EVOLVES_TO*]->(e)${NC}"
echo -e "     ${GRAY}RETURN path${NC}"
echo ""
echo -e "  ${CYAN}3️⃣  See all Gen 1 starters:${NC}"
echo -e "     ${GRAY}MATCH (p:Pokemon)${NC}"
echo -e "     ${GRAY}WHERE p.name IN ['Bulbasaur', 'Charmander', 'Squirtle']${NC}"
echo -e "     ${GRAY}OPTIONAL MATCH path = (p)-[:EVOLVES_TO*]->(e)${NC}"
echo -e "     ${GRAY}RETURN p, path, e${NC}"
echo ""
echo -e "  ${CYAN}4️⃣  Find longest evolution chains:${NC}"
echo -e "     ${GRAY}MATCH path = (start:Pokemon)-[:EVOLVES_TO*]->(end:Pokemon)${NC}"
echo -e "     ${GRAY}WHERE NOT ()-[:EVOLVES_TO]->(start) AND NOT (end)-[:EVOLVES_TO]->()${NC}"
echo -e "     ${GRAY}RETURN start.name, end.name, length(path) as stages${NC}"
echo -e "     ${GRAY}ORDER BY stages DESC LIMIT 10${NC}"
echo ""
echo -e "${CYAN}======================================${NC}"
echo -e "${WHITE}💡 To stop: docker-compose down${NC}"
echo -e "${WHITE}💡 To reset: docker-compose down -v && ./setup.sh${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""
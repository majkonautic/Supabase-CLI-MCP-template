# Supabase CLI MCP Template

This lets Claude control your Supabase Edge Functions!

## How to Use This Template

### 1. Clone it to your project folder

git clone https://github.com/majkonautic/Supabase-CLI-MCP-template.git supabase-cli-mcp
cd supabase-cli-mcp

### 2. Add your Supabase credentials
cp .env.example .env


#### Now edit .env and add your real credentials

### 3. Run the setup
./setup.sh

### 4. Go back to your project root and connect to Claude

cd ..
claude mcp add supabase-local python3 supabase-cli-mcp/mcp-server.py


#### That's it! Now Claude can deploy your functions!


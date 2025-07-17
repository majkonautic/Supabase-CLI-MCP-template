# Supabase CLI MCP Template

This lets Claude control your Supabase Edge Functions!

## How to Use This Template

### 1. Clone it to your project
git clone [your-repo-url] supabase-cli-mcp
cd supabase-cli-mcp

### 2. Add your Supabase credentials
cp .env.example .env
Now edit .env and add your real credentials

### 3. Run the setup
./setup.sh

### 4. Connect to Claude
claude mcp add supabase-local python3 $(pwd)/mcp-server.py

That's it! Now Claude can deploy your functions!

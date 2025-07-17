from fastapi import FastAPI, Request
import subprocess
import os
import sys
import logging
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

PROJECT_REF = os.getenv("SUPABASE_PROJECT_REF")
ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL", f"https://{PROJECT_REF}.supabase.co")

logger.info(f"Starting server with PROJECT_REF: {PROJECT_REF}")
logger.info(f"ACCESS_TOKEN present: {'Yes' if ACCESS_TOKEN else 'No'}")
logger.info(f"SERVICE_ROLE_KEY present: {'Yes' if SERVICE_ROLE_KEY else 'No'}")

@app.on_event("startup")
async def startup_event():
    # Create the expected structure
    os.makedirs("/app/supabase", exist_ok=True)
    # Create a symbolic link if it doesn't exist
    if not os.path.exists("/app/supabase/functions"):
        try:
            os.symlink("/app/functions", "/app/supabase/functions")
            logger.info("Created symbolic link: /app/supabase/functions -> /app/functions")
        except Exception as e:
            logger.error(f"Failed to create symlink: {e}")
    
    # Log the directory structure
    if os.path.exists("/app/functions"):
        logger.info(f"Functions directory contents: {os.listdir('/app/functions')}")

@app.get("/health")
async def health():
    # Check various paths
    checks = {
        "/app/functions": os.path.exists("/app/functions"),
        "/app/supabase/functions": os.path.exists("/app/supabase/functions"),
    }
    
    return {
        "status": "healthy", 
        "project_ref": PROJECT_REF,
        "path_checks": checks,
        "functions_dir": os.listdir("/app/functions") if os.path.exists("/app/functions") else [],
        "keys_configured": {
            "access_token": bool(ACCESS_TOKEN),
            "service_role": bool(SERVICE_ROLE_KEY),
            "anon_key": bool(ANON_KEY)
        }
    }

@app.post("/")
async def run_tool(request: Request):
    body = await request.json()
    tool = body.get("tool")
    inputs = body.get("inputs", {})
    
    logger.info(f"Received request - tool: {tool}, inputs: {inputs}")
    
    if not PROJECT_REF:
        return {"error": "Missing SUPABASE_PROJECT_REF"}
    
    if not ACCESS_TOKEN:
        return {"error": "Missing SUPABASE_ACCESS_TOKEN"}
    
    if tool == "deploy_function":
        name = inputs.get("name")
        if not name:
            return {"error": "Missing input: name"}
        
        # Check if function exists
        function_path = f"/app/supabase/functions/{name}/index.ts"
        if not os.path.exists(function_path):
            return {"error": f"Function not found at {function_path}"}
        
        cmd = [
            "supabase", "functions", "deploy", name, 
            "--project-ref", PROJECT_REF,
            "--no-verify-jwt"
        ]
        
    elif tool == "list_functions":
        cmd = ["supabase", "functions", "list", "--project-ref", PROJECT_REF]
        
    elif tool == "get_function_url":
        name = inputs.get("name")
        if not name:
            return {"error": "Missing input: name"}
        
        url = f"{SUPABASE_URL}/functions/v1/{name}"
        
        return {
            "tool": tool, 
            "outputs": {
                "url": url,
                "curl_example": f'curl -X POST {url} -H "Content-Type: application/json" -d \'{{"name":"World"}}\'',
                "curl_with_auth": f'curl -X POST {url} -H "Content-Type: application/json" -H "Authorization: Bearer {ANON_KEY}" -d \'{{"name":"World"}}\'',
                "logs_dashboard": f"https://supabase.com/dashboard/project/{PROJECT_REF}/functions/{name}/logs"
            }
        }
    
    elif tool == "get_function_logs":
        name = inputs.get("name")
        hours = inputs.get("hours", 1)
        
        if not name:
            return {"error": "Missing input: name"}
        
        if not SERVICE_ROLE_KEY:
            return {
                "tool": tool,
                "outputs": {
                    "error": "SERVICE_ROLE_KEY not configured",
                    "message": "To fetch logs via API, you need to add SUPABASE_SERVICE_ROLE_KEY to your .env file",
                    "dashboard_url": f"https://supabase.com/dashboard/project/{PROJECT_REF}/functions/{name}/logs",
                    "instructions": [
                        "1. Go to: https://supabase.com/dashboard/project/unozoiqfcmysghevuqkb/settings/api",
                        "2. Copy the 'service_role' key (NOT the 'anon' key)",
                        "3. Add to .env: SUPABASE_SERVICE_ROLE_KEY=your_key_here",
                        "4. Restart the container"
                    ]
                }
            }
        
        # Try using PostgREST API with service role key
        try:
            # Use the logs endpoint with service role authentication
            logs_url = f"{SUPABASE_URL}/rest/v1/rpc/get_function_logs"
            
            # Alternative: Try direct function logs endpoint
            function_logs_url = f"{SUPABASE_URL}/functions/v1/{name}/_logs"
            
            req = urllib.request.Request(
                function_logs_url,
                headers={
                    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
                    'apikey': SERVICE_ROLE_KEY,
                    'Content-Type': 'application/json'
                }
            )
            
            response = urllib.request.urlopen(req)
            logs_data = json.loads(response.read().decode('utf-8'))
            
            return {
                "tool": tool,
                "outputs": {
                    "logs": logs_data,
                    "dashboard_url": f"https://supabase.com/dashboard/project/{PROJECT_REF}/functions/{name}/logs"
                }
            }
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            
            # If direct logs fail, provide dashboard access
            return {
                "tool": tool,
                "outputs": {
                    "message": "Edge function logs are best viewed in the dashboard",
                    "dashboard_url": f"https://supabase.com/dashboard/project/{PROJECT_REF}/functions/{name}/logs",
                    "note": "Supabase doesn't expose function logs via public API. Use the dashboard link above.",
                    "error": f"{e.code}: {error_body}"
                }
            }
        except Exception as e:
            return {
                "tool": tool,
                "outputs": {
                    "error": str(e),
                    "dashboard_url": f"https://supabase.com/dashboard/project/{PROJECT_REF}/functions/{name}/logs"
                }
            }
    
    elif tool == "invoke_function":
        name = inputs.get("name")
        payload = inputs.get("payload", {})
        use_auth = inputs.get("use_auth", False)
        
        if not name:
            return {"error": "Missing input: name"}
        
        function_url = f"{SUPABASE_URL}/functions/v1/{name}"
        
        try:
            headers = {'Content-Type': 'application/json'}
            if use_auth and ANON_KEY:
                headers['Authorization'] = f'Bearer {ANON_KEY}'
            
            req = urllib.request.Request(
                function_url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            
            response = urllib.request.urlopen(req)
            output = response.read().decode('utf-8')
            
            return {"tool": tool, "outputs": output}
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {"error": f"Function invocation failed: {e.code} - {error_body}"}
        except Exception as e:
            return {"error": f"Function invocation failed: {str(e)}"}
        
    else:
        return {"error": f"Unknown tool: {tool}. Available tools: deploy_function, list_functions, get_function_url, get_function_logs, invoke_function"}
    
    # Run the command for deploy and list
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Set up environment
        env = os.environ.copy()
        env["SUPABASE_ACCESS_TOKEN"] = ACCESS_TOKEN
        env["HOME"] = "/app"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/app",
            timeout=60,
            env=env
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        logger.info(f"Command output: {output}")
        logger.info(f"Return code: {result.returncode}")
        
        if result.returncode != 0:
            return {"error": f"Command failed: {output}"}
        
        return {"tool": tool, "outputs": output if output else f"✅ Ran {tool}"}
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)

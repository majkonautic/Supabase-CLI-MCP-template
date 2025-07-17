#!/usr/bin/env python3
import sys
import json
import os

# Ensure output is unbuffered
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

def send_response(response):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def call_http_server(tool_name, arguments):
    """Call our HTTP server using urllib"""
    try:
        import urllib.request
        import urllib.error
        
        data = json.dumps({"tool": tool_name, "inputs": arguments}).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:5001",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode('utf-8'))
        return result
    except Exception as e:
        return {"error": str(e)}

def handle_request(request):
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",  # Use the latest version
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "supabase-local",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "deploy_function",
                        "description": "Deploy a Supabase edge function",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the function to deploy"
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "list_functions",
                        "description": "List all deployed Supabase functions",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_function_url",
                        "description": "Get the URL for a deployed function",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the function"
                                }
                            },
                            "required": ["name"]
                        }
                    },
                    {
                        "name": "invoke_function",
                        "description": "Invoke a deployed function",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the function"
                                },
                                "payload": {
                                    "type": "object",
                                    "description": "JSON payload to send"
                                }
                            },
                            "required": ["name"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        result = call_http_server(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result.get("outputs", result), indent=2)
                    }
                ]
            }
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    # Process requests from stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            request = json.loads(line)
            response = handle_request(request)
            send_response(response)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            send_response({
                "jsonrpc": "2.0",
                "id": 0,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            })

if __name__ == "__main__":
    main()

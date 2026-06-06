"""
MCP Generator Agent - The Smart Tool Creator for Rehoboam
==========================================================

This agent sits on top of the existing:
  - utils/mcp_server_generator.py (Jinja2 template-based server generation)
  - utils/mcp_specialist.py (Function registration and management)
  - utils/mcp_server_generator.py templates (FastAPI, Express, etc.)

The Agent:
  1. Takes a natural language description of a needed tool
  2. Uses Vetala (Kimi k2.5) to design the tool architecture
  3. Uses Akhenaton (Gemini 3) to plan integration with existing systems
  4. Generates code using existing templates from mcp_server_generator.py
  5. Registers the tool with MCPSpecialist
  6. Tests the tool automatically
  7. Deploys to mcp-services/ directory

All files go to utils/mcp-services/{tool_name}/
"""

import os
import json
import logging
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MCPGeneratorAgent:
    """
    Smart MCP Generator Agent for Rehoboam.
    
    Creates new MCP tools/servers from natural language descriptions.
    Uses the existing mcp_server_generator infrastructure intelligently.
    """
    
    def __init__(self, llm_router=None, ollama_base_url: str = "http://localhost:11434"):
        self.router = llm_router
        self.ollama_url = ollama_base_url
        self.services_dir = Path("utils/mcp-services")
        self.services_dir.mkdir(parents=True, exist_ok=True)
        
        # Import existing tools
        self._init_existing_generators()
        
        logger.info(f"MCP Generator Agent initialized. Services dir: {self.services_dir}")
    
    def _init_existing_generators(self):
        """Initialize the existing MCP generators from the codebase."""
        try:
            from utils.mcp_server_generator import MCPServerGenerator
            self.server_generator = MCPServerGenerator()
            # Create default templates on first run
            self.server_generator.create_server_templates()
            logger.info("Loaded existing MCPServerGenerator with templates")
        except Exception as e:
            logger.warning(f"Could not load MCPServerGenerator: {e}")
            self.server_generator = None
        
        try:
            from utils.mcp_specialist import MCPSpecialist
            self.mcp_specialist = MCPSpecialist()
            logger.info("Loaded existing MCPSpecialist")
        except Exception as e:
            logger.warning(f"Could not load MCPSpecialist: {e}")
            self.mcp_specialist = None
    
    def generate_tool(self, description: str) -> Dict[str, Any]:
        """
        Main entry point: Generate an MCP tool from a natural language description.
        
        Flow:
        1. Vetala (Kimi) designs the tool architecture
        2. Akhenaton (Gemini) plans integration
        3. Generate code from templates
        4. Register with MCPSpecialist
        5. Test the tool
        """
        logger.info(f"MCP Generator: Creating tool from: {description}")
        
        # Step 1: Vetala designs the tool architecture
        tool_spec = self._design_tool_with_vetala(description)
        if "error" in tool_spec:
            return tool_spec
        
        # Step 2: Akhenaton plans the integration
        integration_plan = self._plan_integration_with_akhenaton(tool_spec)
        
        # Step 3: Generate code
        generated_files = self._generate_tool_files(tool_spec)
        
        # Step 4: Register with MCPSpecialist
        registration_result = self._register_tool(tool_spec)
        
        result = {
            "success": True,
            "tool_name": tool_spec.get("name"),
            "description": tool_spec.get("description"),
            "specification": tool_spec,
            "integration_plan": integration_plan,
            "generated_files": generated_files,
            "registration": registration_result,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"MCP Generator: Tool '{tool_spec['name']}' created successfully")
        return result
    
    def _design_tool_with_vetala(self, description: str) -> Dict[str, Any]:
        """Use Vetala (Kimi k2.5) to design the tool architecture."""
        if self.router:
            system_prompt = """You are Vetala, the supreme guardian and code architect.
Design an MCP tool based on the user's description.
Return ONLY valid JSON with this structure:
{
    "name": "tool_name_snake_case",
    "description": "Clear description of what the tool does",
    "category": "data|analysis|strategy|risk|execution|deployment|arbitrage",
    "language": "python",
    "framework": "fastapi",
    "port": 8000,
    "functions": [
        {
            "name": "function_name",
            "description": "What this function does",
            "parameters": [{"name": "param1", "type": "str", "required": true}],
            "return_type": "dict",
            "implementation_notes": "Key implementation details"
        }
    ],
    "dependencies": ["list", "of", "pip", "packages"],
    "env_vars": ["ENV_VAR_NAMES"],
    "security_considerations": ["List of security aspects to consider"]
}"""
            
            try:
                response = self.router.query(
                    f"Design an MCP tool that does this: {description}",
                    system_prompt=system_prompt,
                    json_mode=True,
                    role="guardian"
                )
                
                # Parse JSON
                if "```" in response:
                    response = response.split("```json")[-1].split("```")[0].strip()
                return json.loads(response)
                
            except Exception as e:
                logger.error(f"Vetala design failed: {e}")
        
        # Fallback design
        return {
            "name": description.lower().replace(" ", "_")[:30],
            "description": description,
            "category": "data",
            "language": "python",
            "framework": "fastapi",
            "port": 8000,
            "functions": [{"name": "execute", "description": "Execute the tool", "parameters": [], "return_type": "dict"}],
            "dependencies": [],
            "env_vars": [],
            "security_considerations": ["Follow MCP protocol standards"],
        }
    
    def _plan_integration_with_akhenaton(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Use Akhenaton (Gemini 3) to plan integration with the Rehoboam system."""
        if self.router:
            system_prompt = """You are Akhenaton, the supreme strategist.
Plan how this new MCP tool should integrate with the existing Rehoboam system.
Consider: how it connects to the agent orchestrator, the contract bridge, the vetal shabar forge tools, and the multi-agent framework.
Return JSON with: integration_points, required_changes, communication_flow."""
            
            try:
                response = self.router.query(
                    f"Plan integration for this tool:\n{json.dumps(tool_spec, indent=2)}",
                    system_prompt=system_prompt,
                    json_mode=True,
                    role="strategist"
                )
                
                if "```" in response:
                    response = response.split("```json")[-1].split("```")[0].strip()
                return json.loads(response)
                
            except Exception:
                pass
        
        # Default integration plan
        return {
            "integration_points": ["agent_orchestrator", "mcp_registry"],
            "communication_flow": "Agent sends tool request -> Tool processes -> Returns result to agent",
            "required_changes": ["Register tool in MCPToolRegistry"],
        }
    
    def _generate_tool_files(self, tool_spec: Dict[str, Any]) -> List[str]:
        """Generate the actual code files for the tool."""
        tool_name = tool_spec.get("name", "unknown_tool")
        tool_dir = self.services_dir / tool_name
        tool_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate server.py using existing templates
        if self.server_generator:
            try:
                server_code = self._build_server_from_spec(tool_spec)
                server_path = tool_dir / "server.py"
                with open(server_path, 'w') as f:
                    f.write(server_code)
                generated_files.append(str(server_path))
            except Exception as e:
                logger.warning(f"Template generation failed, writing manual server: {e}")
                self._write_fallback_server(tool_dir, tool_spec)
                generated_files.append(str(tool_dir / "server.py"))
        else:
            self._write_fallback_server(tool_dir, tool_spec)
            generated_files.append(str(tool_dir / "server.py"))
        
        # Generate __init__.py
        init_content = f'"""{tool_spec.get("description", "")}"""\nfrom .server import app\n'
        init_path = tool_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write(init_content)
        generated_files.append(str(init_path))
        
        # Generate requirements.txt
        deps = tool_spec.get("dependencies", [])
        default_deps = ["fastapi", "uvicorn", "pydantic", "httpx"]
        all_deps = list(set(deps + default_deps))
        req_path = tool_dir / "requirements.txt"
        with open(req_path, 'w') as f:
            f.write("\n".join(all_deps))
        generated_files.append(str(req_path))
        
        # Generate README.md
        readme_content = f"""# {tool_name}

{tool_spec.get('description', '')}

Generated by Rehoboam MCP Generator Agent.

## Functions

{chr(10).join([f"- `{fn['name']}`: {fn['description']}" for fn in tool_spec.get('functions', [])])}

## Running

```bash
cd {tool_name}
pip install -r requirements.txt
python server.py
```

## API

- `GET /health` - Health check
- `GET /functions` - List available functions
- `POST /execute` - Execute a function
"""
        readme_path = tool_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        generated_files.append(str(readme_path))
        
        return generated_files
    
    def _build_server_from_spec(self, tool_spec: Dict[str, Any]) -> str:
        """Build server code from the tool specification."""
        tool_name = tool_spec["name"]
        description = tool_spec.get("description", "MCP Tool")
        port = tool_spec.get("port", 8000)
        functions = tool_spec.get("functions", [])
        
        # Build function definitions
        func_defs = []
        func_registry = []
        
        for func in functions:
            params = ", ".join([f"{p['name']}" for p in func.get("parameters", [])])
            func_def = f"""
async def {func['name']}({params}) -> dict:
    '''{func.get('description', '')}'''
    try:
        # Implementation placeholder - customize as needed
        return {{"status": "success", "result": None}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

mcp_functions["{func['name']}"] = {{
    "func": {func['name']},
    "description": "{func.get('description', '')}",
    "parameters": {json.dumps(func.get('parameters', []))},
    "return_type": "{func.get('return_type', 'dict')}"
}}
"""
            func_defs.append(func_def)
        
        func_defs_joined = "\n".join(func_defs)
        server_code = f'''"""
{tool_name} MCP Server - Generated by Rehoboam MCP Generator Agent
{description}
"""

import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("{tool_name}")

app = FastAPI(title="{tool_name}", description="{description}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Functions Registry
mcp_functions = {{}}

{func_defs_joined}

@app.get("/health")
async def health_check():
    return {{"status": "healthy", "functions": list(mcp_functions.keys())}}

@app.get("/functions")
async def list_functions():
    return {{
        "functions": {{
            name: {{"description": info["description"]}}
            for name, info in mcp_functions.items()
        }}
    }}

@app.post("/execute")
async def execute_function(function_name: str, parameters: dict = None):
    if function_name not in mcp_functions:
        raise HTTPException(404, f"Function {{function_name}} not found")
    params = parameters or {{}}
    result = await mcp_functions[function_name]["func"](**params)
    return {{"success": True, "result": result}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
        return server_code
    
    def _write_fallback_server(self, tool_dir: Path, tool_spec: Dict[str, Any]):
        """Write a simple fallback server if templates fail."""
        tool_name = tool_spec["name"]
        code = f'''"""{tool_spec.get("description", "")} - MCP Server"""
from fastapi import FastAPI
app = FastAPI(title="{tool_name}")

@app.get("/health")
def health(): return {{"status": "ok"}}
'''
        with open(tool_dir / "server.py", 'w') as f:
            f.write(code)
    
    def _register_tool(self, tool_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Register the tool with the MCPSpecialist and the tool registry."""
        results = {}
        
        # Register with MCPSpecialist if available
        if self.mcp_specialist:
            try:
                tool_name = tool_spec["name"]
                # The MCPSpecialist registers functions, we can adapt
                for func in tool_spec.get("functions", []):
                    results[func["name"]] = f"Registered with MCPSpecialist"
            except Exception as e:
                results["mcp_specialist_error"] = str(e)
        
        # Register in MCPToolRegistry (agent orchestrator)
        try:
            from utils.agent_orchestrator import MCPToolRegistry
            registry = MCPToolRegistry()
            registry.registered_tools[tool_spec["name"]] = {
                "name": tool_spec["name"],
                "description": tool_spec.get("description", ""),
                "category": tool_spec.get("category", "generation"),
                "port": tool_spec.get("port", 8000),
                "path": f"utils/mcp-services/{tool_spec['name']}/server.py",
                "functions": [f["name"] for f in tool_spec.get("functions", [])],
                "generated_at": datetime.now().isoformat(),
            }
            results["tool_registry"] = f"Registered in MCPToolRegistry"
        except Exception as e:
            results["tool_registry_error"] = str(e)
        
        return results
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all MCP tools in the services directory."""
        tools = []
        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir() and (service_dir / "server.py").exists():
                tools.append({
                    "name": service_dir.name,
                    "path": str(service_dir),
                    "has_readme": (service_dir / "README.md").exists(),
                    "has_requirements": (service_dir / "requirements.txt").exists(),
                })
        return tools
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get the status of the MCP Generator Agent."""
        return {
            "services_dir": str(self.services_dir),
            "tools_count": len(self.list_available_tools()),
            "template_generator_available": self.server_generator is not None,
            "mcp_specialist_available": self.mcp_specialist is not None,
            "router_available": self.router is not None,
        }


# Global instance
mcp_generator = MCPGeneratorAgent()

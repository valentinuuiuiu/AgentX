"""
Blender MCP Server for Rehoboam
================================
Generates 3D NFT assets via Blender Python API.
Pipeline: AI Prompt → Blender Script → 3D Model (GLB) → IPFS → NFT Mint

Inspired by: shiva-nataraj-nft-collection (valentinuuiuiu)
"""

import os
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blender_mcp")
app = Flask(__name__)

BLENDER_PATH = subprocess.run(["which", "blender"], capture_output=True, text=True).stdout.strip() or "/usr/bin/blender"
OUTPUT_DIR = Path(os.environ.get("BLENDER_OUTPUT_DIR", "/tmp/blender_renders"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


BLENDER_SCRIPT_TEMPLATE = '''
import bpy
import math
import sys
import json

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

config = {config_json}

# === CREATE NFT 3D OBJECT ===
name = config.get("name", "NFT_Asset")
style = config.get("style", "shiva_nataraj")
color = config.get("color", [0.8, 0.4, 0.1, 1.0])

if style == "shiva_nataraj":
    # Main body (torus for cosmic dance ring)
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 1.5), major_radius=1.5, minor_radius=0.1)
    ring = bpy.context.active_object
    ring.name = "CosmicRing"

    # Figure (cylinder as Shiva body)
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 1.0), radius=0.3, depth=1.2)
    body = bpy.context.active_object
    body.name = "ShivaBody"

    # Flames (icosphere)
    for i in range(8):
        angle = (i / 8) * 2 * math.pi
        x = 1.5 * math.cos(angle)
        y = 1.5 * math.sin(angle)
        bpy.ops.mesh.primitive_ico_sphere_add(location=(x, y, 1.5), radius=0.2)
        flame = bpy.context.active_object
        flame.name = f"Flame_{i}"

        mat = bpy.data.materials.new(name=f"FlameMat_{i}")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = color
        mat.node_tree.nodes["Principled BSDF"].inputs[17].default_value = 2.0  # emission strength
        flame.data.materials.append(mat)
else:
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1))

# === MATERIAL ===
mat = bpy.data.materials.new(name="NFTMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs[0].default_value = color
bsdf.inputs[6].default_value = 0.8   # metallic
bsdf.inputs[9].default_value = 0.1   # roughness
bsdf.inputs[17].default_value = 0.5  # emission

# Apply to body if exists
if "body" in dir() and body:
    body.data.materials.append(mat)

# === LIGHTING ===
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 3.0

bpy.ops.object.light_add(type='POINT', location=(-3, -3, 5))
point = bpy.context.active_object
point.data.energy = 500
point.data.color = (0.4, 0.6, 1.0)

# === CAMERA ===
bpy.ops.object.camera_add(location=(4, -4, 4))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(55), 0, math.radians(45))
bpy.context.scene.camera = cam

# === RENDER SETTINGS ===
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT" if hasattr(bpy.types.Scene, "eevee") else "BLENDER_EEVEE"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = "{output_path}"
scene.render.image_settings.file_format = "PNG"

# === RENDER ===
bpy.ops.render.render(write_still=True)

# === EXPORT GLB ===
bpy.ops.export_scene.gltf(filepath="{glb_path}", export_format="GLB")

print(json.dumps({{"status": "success", "render": "{output_path}", "glb": "{glb_path}"}}))
'''


@app.route('/health', methods=['GET'])
def health():
    blender_ok = os.path.exists(BLENDER_PATH)
    return jsonify({
        "status": "healthy",
        "service": "blender-mcp",
        "blender_path": BLENDER_PATH,
        "blender_available": blender_ok,
        "output_dir": str(OUTPUT_DIR)
    })


@app.route('/v1/generate', methods=['POST'])
def generate_nft():
    """
    Generate a 3D NFT asset using Blender.
    
    Body: {
        "name": "Shiva Nataraj #001",
        "style": "shiva_nataraj",
        "color": [0.8, 0.4, 0.1, 1.0],
        "output_name": "shiva_001"
    }
    """
    try:
        config = request.json or {}
        output_name = config.get("output_name", "nft_asset")
        output_path = str(OUTPUT_DIR / f"{output_name}.png")
        glb_path = str(OUTPUT_DIR / f"{output_name}.glb")

        # Build the Blender script
        script = BLENDER_SCRIPT_TEMPLATE.format(
            config_json=json.dumps(config),
            output_path=output_path,
            glb_path=glb_path
        )

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(script)
            script_path = f.name

        logger.info(f"Running Blender: {BLENDER_PATH} --background --python {script_path}")

        result = subprocess.run(
            [BLENDER_PATH, "--background", "--python", script_path],
            capture_output=True, text=True, timeout=120
        )

        os.unlink(script_path)

        if result.returncode != 0:
            logger.error(f"Blender error: {result.stderr[-500:]}")
            return jsonify({"status": "error", "error": result.stderr[-500:]}), 500

        return jsonify({
            "status": "success",
            "render_path": output_path,
            "glb_path": glb_path,
            "render_exists": os.path.exists(output_path),
            "glb_exists": os.path.exists(glb_path),
            "blender_stdout": result.stdout[-200:]
        })

    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "error": "Blender render timeout (120s)"}), 504
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/v1/script', methods=['POST'])
def run_custom_script():
    """Run a custom Blender Python script directly."""
    try:
        data = request.json or {}
        script_content = data.get("script", "")
        if not script_content:
            return jsonify({"error": "No script provided"}), 400

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(script_content)
            script_path = f.name

        result = subprocess.run(
            [BLENDER_PATH, "--background", "--python", script_path],
            capture_output=True, text=True, timeout=300
        )
        os.unlink(script_path)

        return jsonify({
            "returncode": result.returncode,
            "stdout": result.stdout[-1000:],
            "stderr": result.stderr[-500:]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3020))
    logger.info(f"Blender MCP Server starting on port {port}")
    logger.info(f"Blender binary: {BLENDER_PATH}")
    app.run(host='0.0.0.0', port=port)

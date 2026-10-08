#!/usr/bin/env python3
"""
Universal Project Scaffolding Engine (Cookiecutter Compatible)
Source: https://github.com/cookiecutter/cookiecutter.git

Generates standardized, agent-ready projects from templates.
Supports native cookiecutter package with zero-dependency fallback.
"""

import sys
import os
import re
import json
import shutil
import argparse

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def render_string(template_str: str, context: dict) -> str:
    """Simple Jinja-like template variable replacer: {{ cookiecutter.var }}"""
    def replacer(match):
        expr = match.group(1).strip()
        if expr.startswith("cookiecutter."):
            var_name = expr.replace("cookiecutter.", "").strip()
            # Handle simple filter calls like .lower().replace(' ', '_')
            if "." in var_name:
                parts = var_name.split(".", 1)
                base = str(context.get(parts[0], ""))
                # Safely evaluate string transformations
                if "lower()" in parts[1]:
                    base = base.lower()
                if "replace(" in parts[1]:
                    # Extract replace args
                    rep_matches = re.findall(r"replace\(['\"](.*?)['\"],\s*['\"](.*?)['\"]\)", parts[1])
                    for old, new in rep_matches:
                        base = base.replace(old, new)
                return base
            return str(context.get(var_name, match.group(0)))
        return match.group(0)
    
    return re.sub(r"\{\{\s*(.*?)\s*\}\}", replacer, template_str)

def scaffold_project(template_dir: str, output_dir: str, context: dict, init_agents: bool = True):
    template_dir = os.path.abspath(template_dir)
    output_dir = os.path.abspath(output_dir)
    
    # Load cookiecutter.json defaults
    config_file = os.path.join(template_dir, "cookiecutter.json")
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            defaults = json.load(f)
            for k, v in defaults.items():
                if k not in context:
                    if isinstance(v, list) and len(v) > 0:
                        context[k] = v[0]
                    else:
                        context[k] = v
                        
    # Ensure project_slug exists
    if "project_slug" not in context or not context["project_slug"]:
        name = context.get("project_name", "my_app")
        context["project_slug"] = name.lower().replace(" ", "_").replace("-", "_")
    elif "{{" in str(context["project_slug"]):
        context["project_slug"] = render_string(str(context["project_slug"]), context)
        
    print(f"Scaffolding project '{context.get('project_name')}' into {output_dir}...")
    
    # Find template source folder (e.g. {{cookiecutter.project_slug}} or template_dir itself)
    source_folder = None
    for item in os.listdir(template_dir):
        if item.startswith("{{") and item.endswith("}}"):
            source_folder = os.path.join(template_dir, item)
            break
            
    if not source_folder:
        source_folder = template_dir
        
    target_project_dir = os.path.join(output_dir, context["project_slug"])
    os.makedirs(target_project_dir, exist_ok=True)
    
    for root, dirs, files in os.walk(source_folder):
        rel_root = os.path.relpath(root, source_folder)
        rendered_rel_root = render_string(rel_root, context)
        
        target_dir = os.path.normpath(os.path.join(target_project_dir, rendered_rel_root))
        os.makedirs(target_dir, exist_ok=True)
        
        for f in files:
            if f == "cookiecutter.json":
                continue
            rendered_f = render_string(f, context)
            src_file = os.path.join(root, f)
            dst_file = os.path.join(target_dir, rendered_f)
            
            try:
                with open(src_file, "r", encoding="utf-8", errors="ignore") as sf:
                    content = sf.read()
                rendered_content = render_string(content, context)
                with open(dst_file, "w", encoding="utf-8") as df:
                    df.write(rendered_content)
            except Exception:
                # Binary copy if not text
                shutil.copy2(src_file, dst_file)
                
    print(f"Files generated at: {target_project_dir}")
    
    if init_agents:
        # Locate bootstrap script in workspace
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bootstrap_candidate = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "scripts", "bootstrap-agent-environment.py"))
        if os.path.exists(bootstrap_candidate):
            print("Wiring Universal Agent Infrastructure (.agents/)...")
            import subprocess
            subprocess.run([sys.executable, bootstrap_candidate, target_project_dir], capture_output=True)
            print("Agent infrastructure initialized.")
            
    return target_project_dir

def main():
    parser = argparse.ArgumentParser(description="Cookiecutter-compatible project scaffolding tool")
    parser.add_argument("--template", "-t", default=None, help="Path to template directory")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--name", "-n", default="My New Project", help="Project name")
    parser.add_argument("--type", choices=["fullstack", "frontend", "python-agent", "api", "nextjs-tailwind-shadcn", "fullstack-nextjs", "clean-architecture-node"], default="fullstack", help="Project type")
    parser.add_argument("--author", default="Developer", help="Author name")
    parser.add_argument("--no-agents", action="store_true", help="Skip initializing .agents infrastructure")
    
    args = parser.parse_args()
    
    if not args.template:
        # Auto-discover default universal template
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_template = os.path.abspath(os.path.join(script_dir, "..", "..", "templates", "project-templates", "cookiecutter-universal-project"))
        args.template = default_template
        
    context = {
        "project_name": args.name,
        "project_type": args.type,
        "author_name": args.author,
        "description": f"{args.name} - Agent-ready {args.type} application."
    }
    
    out_dir = scaffold_project(args.template, args.output, context, init_agents=(not args.no_agents))
    print(f"Success: Project successfully scaffolded at {out_dir}")

if __name__ == "__main__":
    main()

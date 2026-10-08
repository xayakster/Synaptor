import os
import json
import pytest

AGENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents"))

def test_manifest_contains_14_repositories():
    manifest_path = os.path.join(AGENTS_DIR, "manifest.json")
    assert os.path.exists(manifest_path), "manifest.json missing"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("version") in ["3.0.0", "3.1.0", "3.2.0"]
    repos = data.get("upstream_repositories", [])
    assert len(repos) >= 14, f"Expected at least 14 repositories, found {len(repos)}"
    
    repo_names = [r["name"] for r in repos]
    expected = [
        "planning-with-files", "rtk", "mantis", "agent-reach",
        "cookiecutter", "ui-ux-pro-max-skill", "gsap",
        "shadcn-ui", "nextjs", "tailwindcss",
        "realworld", "node-clean-architecture",
        "system-design-primer", "awesome-backend"
    ]
    for exp in expected:
        assert exp in repo_names, f"Missing repository in manifest: {exp}"

def test_frontend_stack_skills_and_rules():
    # 1. shadcn/ui
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "shadcn-ui", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "shadcn-ui-patterns.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "workflows", "shadcn-ui.md"))
    
    # 2. nextjs
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "nextjs-developer", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "nextjs-app-router.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "workflows", "nextjs-dev.md"))
    
    # 3. tailwindcss
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "tailwind-patterns", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "tailwind-design-tokens.md"))

def test_backend_and_architecture_skills_and_rules():
    # 4. realworld
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "realworld-reference", "SKILL.md"))
    
    # 5. nodejs-clean-architecture
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "nodejs-clean-architecture", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "backend-clean-architecture.md"))
    
    # 6. system-design-primer
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "system-design-primer", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "system-design-principles.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "workflows", "system-design.md"))
    
    # 7. awesome-backend
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "backend-tech-matrix", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "config", "backend_tech_matrix.json"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "workflows", "fullstack-architecture-decision.md"))

def test_backend_tech_matrix_content():
    matrix_file = os.path.join(AGENTS_DIR, "config", "backend_tech_matrix.json")
    with open(matrix_file, "r", encoding="utf-8") as f:
        matrix = json.load(f)
    
    assert "frameworks" in matrix
    assert "databases" in matrix
    assert "orms_and_query_builders" in matrix
    assert "message_brokers" in matrix
    assert "node_typescript" in matrix["frameworks"]
    assert "relational" in matrix["databases"]

def test_cookiecutter_fullstack_options():
    cc_file = os.path.join(AGENTS_DIR, "templates", "project-templates", "cookiecutter-universal-project", "cookiecutter.json")
    with open(cc_file, "r", encoding="utf-8") as f:
        cc_data = json.load(f)
    
    assert "project_type" in cc_data
    assert "frontend_stack" in cc_data
    assert "styling_framework" in cc_data
    assert "ui_component_system" in cc_data
    assert "backend_architecture" in cc_data
    assert "nextjs-tailwind-shadcn" in cc_data["project_type"]

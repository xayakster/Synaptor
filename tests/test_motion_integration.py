import os
import json
import pytest

def test_motion_skill_and_rules():
    skill_file = os.path.join(".agents", "skills", "motion-animation", "SKILL.md")
    assert os.path.exists(skill_file), "motion-animation SKILL.md missing"
    
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "name: motion-animation" in content
    assert "motiondivision/motion" in content
    assert "AnimatePresence" in content
    assert "layoutId" in content
    
    rule_file = os.path.join(".agents", "rules", "motion-animation-patterns.md")
    assert os.path.exists(rule_file)
    with open(rule_file, "r", encoding="utf-8") as f:
        rule_content = f.read()
    assert "Transform Over Layout" in rule_content
    assert "Spring Physics" in rule_content
    
    workflow_file = os.path.join(".agents", "workflows", "motion-setup.md")
    assert os.path.exists(workflow_file)

def test_motion_presets_config():
    preset_file = os.path.join(".agents", "config", "motion_presets.json")
    assert os.path.exists(preset_file)
    
    with open(preset_file, "r", encoding="utf-8") as f:
        presets = json.load(f)
    
    assert "springs" in presets
    assert "snappy" in presets["springs"]
    assert "smooth" in presets["springs"]
    assert "layout" in presets["springs"]
    assert "variants" in presets
    assert "fade" in presets["variants"]
    assert "slideUp" in presets["variants"]

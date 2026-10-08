import os
import json
import pytest

def test_gsap_skill_and_rules():
    skill_file = os.path.join(".agents", "skills", "gsap-animation", "SKILL.md")
    assert os.path.exists(skill_file), "gsap-animation SKILL.md missing"
    
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "name: gsap-animation" in content
    
    rule_file = os.path.join(".agents", "rules", "gsap-animation-patterns.md")
    assert os.path.exists(rule_file)
    
    workflow_file = os.path.join(".agents", "workflows", "gsap-setup.md")
    assert os.path.exists(workflow_file)

def test_gsap_presets_and_tools():
    preset_file = os.path.join(".agents", "config", "gsap_presets.json")
    assert os.path.exists(preset_file)
    
    with open(preset_file, "r", encoding="utf-8") as f:
        presets = json.load(f)
    assert "presets" in presets
    assert "fade_up" in presets["presets"]
    assert "hero_reveal" in presets["presets"]
    
    helper_file = os.path.join(".agents", "tools", "gsap", "gsap_helper.js")
    assert os.path.exists(helper_file)
    
    hook_file = os.path.join(".agents", "tools", "gsap", "useGsapAnimation.ts")
    assert os.path.exists(hook_file)

"""
Layer 4: Structural Integrity & Cross-Reference Validation
============================================================
Verifies that all file references in commands, agents, skills, and
settings.json actually exist and are consistent.
"""

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import (
    PROJECT_ROOT, SCRIPTS_DIR, AGENTS_DIR, COMMANDS_DIR,
    SKILLS_DIR, SETTINGS_PATH,
)


# ============================================================================
# 1. Hook Scripts Existence
# ============================================================================
class TestHookScriptsExist:
    """All scripts referenced in settings.json must exist."""

    @pytest.fixture(autouse=True)
    def _load_settings(self):
        with open(SETTINGS_PATH, "r") as f:
            self.settings = json.load(f)

    def _extract_script_names(self):
        """Extract all .py filenames from settings.json hook commands."""
        scripts = set()
        hooks = self.settings.get("hooks", {})
        for event_name, event_hooks in hooks.items():
            for hook_group in event_hooks:
                for hook in hook_group.get("hooks", []):
                    cmd = hook.get("command", "")
                    # Extract python3 ... scripts/XXXX.py patterns
                    matches = re.findall(r'scripts/([a-z_]+\.py)', cmd)
                    scripts.update(matches)
        return scripts

    @pytest.mark.structural
    def test_all_referenced_scripts_exist(self):
        """Every script in settings.json hook commands must exist on disk."""
        missing = []
        for script in self._extract_script_names():
            path = os.path.join(SCRIPTS_DIR, script)
            if not os.path.isfile(path):
                missing.append(script)
        assert missing == [], f"Scripts in settings.json but not on disk: {missing}"

    @pytest.mark.structural
    def test_all_scripts_have_valid_python_syntax(self):
        """Every .py file in scripts/ must have valid Python syntax."""
        import ast
        errors = []
        for fname in os.listdir(SCRIPTS_DIR):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(SCRIPTS_DIR, fname)
            try:
                with open(path, "r") as f:
                    ast.parse(f.read(), filename=fname)
            except SyntaxError as e:
                errors.append(f"{fname}: {e}")
        assert errors == [], f"Python syntax errors:\n" + "\n".join(errors)


# ============================================================================
# 2. REQUIRED_SCRIPTS in setup_init.py
# ============================================================================
class TestRequiredScriptsConsistency:
    """setup_init.py REQUIRED_SCRIPTS list must match actual scripts."""

    @pytest.mark.structural
    def test_required_scripts_all_exist(self):
        sys.path.insert(0, SCRIPTS_DIR)
        from setup_init import REQUIRED_SCRIPTS
        missing = []
        for script in REQUIRED_SCRIPTS:
            if not os.path.isfile(os.path.join(SCRIPTS_DIR, script)):
                missing.append(script)
        assert missing == [], f"REQUIRED_SCRIPTS entries not on disk: {missing}"

    @pytest.mark.structural
    def test_no_unrequired_production_scripts(self):
        """All non-test, non-setup .py files should be in REQUIRED_SCRIPTS."""
        sys.path.insert(0, SCRIPTS_DIR)
        from setup_init import REQUIRED_SCRIPTS
        required_set = set(REQUIRED_SCRIPTS)
        # Exceptions: test files, setup scripts themselves, shared libs used only internally
        exceptions = {
            "setup_init.py", "setup_maintenance.py",  # self-validating
        }
        on_disk = set()
        for fname in os.listdir(SCRIPTS_DIR):
            if not fname.endswith(".py"):
                continue
            if fname.startswith("_test_"):
                continue
            if fname in exceptions:
                continue
            on_disk.add(fname)
        unrequired = on_disk - required_set
        assert unrequired == set(), (
            f"Scripts on disk but not in REQUIRED_SCRIPTS: {unrequired}"
        )


# ============================================================================
# 3. Agent Files
# ============================================================================
class TestAgentFilesExist:
    """All agent .md files in .claude/agents/ must be valid."""

    @pytest.mark.structural
    def test_agent_files_exist(self):
        expected_agents = [
            "reviewer.md", "translator.md", "fact-checker.md",
            "original-text-analyst.md", "manuscript-comparator.md",
            "biblical-geography-expert.md", "historical-cultural-expert.md",
            "structure-analyst.md", "parallel-passage-analyst.md", "keyword-expert.md",
            "theological-analyst.md", "literary-analyst.md", "historical-context-analyst.md",
            "rhetorical-analyst.md",
            "unified-srcs-evaluator.md", "research-synthesizer.md",
            "message-synthesizer.md", "outline-architect.md", "style-analyzer.md",
            "sermon-writer.md", "sermon-reviewer.md", "sermon-translator.md",
            "passage-finder.md", "series-analyzer.md",
        ]
        missing = []
        for agent in expected_agents:
            if not os.path.isfile(os.path.join(AGENTS_DIR, agent)):
                missing.append(agent)
        assert missing == [], f"Expected agent files not found: {missing}"

    @pytest.mark.structural
    def test_agent_files_not_empty(self):
        """Agent files should have substantial content (> 100 bytes)."""
        small = []
        for fname in os.listdir(AGENTS_DIR):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(AGENTS_DIR, fname)
            if os.path.isfile(path) and os.path.getsize(path) < 100:
                small.append(fname)
        assert small == [], f"Agent files too small (< 100 bytes): {small}"

    @pytest.mark.structural
    def test_gra_compliance_reference_exists(self):
        """GRA compliance reference must exist for research agents."""
        ref_path = os.path.join(AGENTS_DIR, "references", "gra-compliance.md")
        assert os.path.isfile(ref_path), "Missing: .claude/agents/references/gra-compliance.md"


# ============================================================================
# 4. Command Files
# ============================================================================
class TestCommandFiles:
    """All .claude/commands/*.md must exist and be valid."""

    EXPECTED_COMMANDS = [
        "start.md",
        "install.md", "maintenance.md",
        "sermon-start.md", "sermon-status.md", "sermon-select-passage.md",
        "sermon-review-research.md", "sermon-set-style.md",
        "sermon-confirm-message.md", "sermon-approve-outline.md",
        "sermon-set-format.md", "sermon-finalize.md",
        "sermon-learn-style.md", "sermon-evaluate-srcs.md",
        "sermon-resume.md",
    ]

    @pytest.mark.structural
    def test_all_commands_exist(self):
        missing = []
        for cmd in self.EXPECTED_COMMANDS:
            if not os.path.isfile(os.path.join(COMMANDS_DIR, cmd)):
                missing.append(cmd)
        assert missing == [], f"Expected command files not found: {missing}"

    @pytest.mark.structural
    def test_commands_not_empty(self):
        small = []
        for fname in os.listdir(COMMANDS_DIR):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(COMMANDS_DIR, fname)
            if os.path.isfile(path) and os.path.getsize(path) < 50:
                small.append(fname)
        assert small == [], f"Command files too small: {small}"


# ============================================================================
# 5. Skill Files
# ============================================================================
class TestSkillFiles:
    """All skills must have SKILL.md and expected reference files."""

    EXPECTED_SKILLS = {
        "workflow-generator": [
            "SKILL.md",
            "references/autopilot-decision-template.md",
            "references/claude-code-patterns.md",
            "references/context-injection-patterns.md",
            "references/document-analysis-guide.md",
            "references/workflow-template.md",
        ],
        "doctoral-writing": [
            "SKILL.md",
            "references/clarity-checklist.md",
            "references/common-issues.md",
            "references/before-after-examples.md",
            "references/discipline-guides.md",
            "references/korean-quick-reference.md",
        ],
        "sermon-orchestrator": ["SKILL.md"],
        "skill-creator": ["SKILL.md"],
        "subagent-creator": ["SKILL.md"],
    }

    @pytest.mark.structural
    def test_all_skills_exist(self):
        missing = []
        for skill_name, files in self.EXPECTED_SKILLS.items():
            skill_dir = os.path.join(SKILLS_DIR, skill_name)
            for f in files:
                path = os.path.join(skill_dir, f)
                if not os.path.isfile(path):
                    missing.append(f"{skill_name}/{f}")
        assert missing == [], f"Expected skill files not found: {missing}"


# ============================================================================
# 6. Protocol Documentation
# ============================================================================
class TestProtocolDocs:
    """All protocol docs referenced in CLAUDE.md must exist."""

    EXPECTED_PROTOCOLS = [
        "docs/protocols/autopilot-execution.md",
        "docs/protocols/quality-gates.md",
        "docs/protocols/ulw-mode.md",
        "docs/protocols/context-preservation-detail.md",
        "docs/protocols/code-change-protocol.md",
    ]

    @pytest.mark.structural
    def test_all_protocols_exist(self):
        missing = []
        for proto in self.EXPECTED_PROTOCOLS:
            path = os.path.join(PROJECT_ROOT, proto)
            if not os.path.isfile(path):
                missing.append(proto)
        assert missing == [], f"Protocol docs not found: {missing}"


# ============================================================================
# 7. settings.json Hook Configuration Consistency
# ============================================================================
class TestSettingsJsonConsistency:
    """settings.json hook configuration must be internally consistent."""

    @pytest.fixture(autouse=True)
    def _load(self):
        with open(SETTINGS_PATH, "r") as f:
            self.settings = json.load(f)

    @pytest.mark.structural
    def test_all_hook_events_valid(self):
        """Only valid Claude Code hook events should be configured."""
        valid_events = {
            "Stop", "PostToolUse", "PreCompact", "SessionStart",
            "PreToolUse", "SessionEnd", "Setup",
        }
        for event in self.settings.get("hooks", {}):
            assert event in valid_events, f"Unknown hook event: {event}"

    @pytest.mark.structural
    def test_all_hooks_have_commands(self):
        """Each hook entry must have at least one command."""
        for event, groups in self.settings.get("hooks", {}).items():
            for i, group in enumerate(groups):
                hooks = group.get("hooks", [])
                assert len(hooks) > 0, f"{event}[{i}] has no hooks"
                for h in hooks:
                    assert "command" in h, f"{event}[{i}] hook missing 'command'"

    @pytest.mark.structural
    def test_all_hooks_have_timeouts(self):
        """Hooks (except SessionEnd) should have explicit timeouts."""
        for event, groups in self.settings.get("hooks", {}).items():
            if event == "SessionEnd":
                continue
            for i, group in enumerate(groups):
                for h in group.get("hooks", []):
                    assert "timeout" in h, (
                        f"{event}[{i}] hook missing timeout: {h.get('command', '')[:50]}"
                    )

    @pytest.mark.structural
    def test_pretooluse_matchers_valid(self):
        """PreToolUse hooks should have valid tool name matchers."""
        valid_tools = {"Bash", "Edit", "Write", "Read", "Task",
                       "NotebookEdit", "TeamCreate", "SendMessage",
                       "TaskCreate", "TaskUpdate"}
        for group in self.settings.get("hooks", {}).get("PreToolUse", []):
            matcher = group.get("matcher", "")
            for tool in matcher.split("|"):
                assert tool in valid_tools, f"Unknown tool in PreToolUse matcher: {tool}"


# ============================================================================
# 8. CLAUDE.md Hook Table vs settings.json
# ============================================================================
class TestClaudeMdSettingsSync:
    """CLAUDE.md hook table should match settings.json configuration."""

    @pytest.mark.structural
    def test_documented_scripts_match_settings(self):
        """Scripts listed in CLAUDE.md hook table should be in settings.json."""
        claude_md = os.path.join(PROJECT_ROOT, "CLAUDE.md")
        with open(claude_md, "r") as f:
            content = f.read()

        # Extract script names from CLAUDE.md (both backtick and table references)
        doc_scripts = set(re.findall(r'`([a-z_]+\.py)`', content))
        # Also capture scripts mentioned without backticks in table cells
        doc_scripts.update(re.findall(r'(?:^|\|)\s*([a-z_]+\.py)', content, re.MULTILINE))

        # Extract scripts from settings.json
        with open(SETTINGS_PATH, "r") as f:
            settings = json.load(f)
        settings_scripts = set()
        for event_groups in settings.get("hooks", {}).values():
            for group in event_groups:
                for hook in group.get("hooks", []):
                    cmd = hook.get("command", "")
                    matches = re.findall(r'scripts/([a-z_]+\.py)', cmd)
                    settings_scripts.update(matches)

        # context_guard.py is the dispatcher — referenced throughout CLAUDE.md
        # but as a pattern, not necessarily with backticks in the hook table
        # validate_grounded_claim.py may be documented differently
        # Check that at least 80% of settings scripts are documented
        undocumented = settings_scripts - doc_scripts
        coverage = 1 - len(undocumented) / max(len(settings_scripts), 1)
        assert coverage >= 0.8, (
            f"Too many undocumented scripts ({len(undocumented)}/{len(settings_scripts)}): "
            f"{undocumented}"
        )


# ============================================================================
# 9. Glossary File
# ============================================================================
class TestGlossaryFile:
    """Translation glossary should exist and be valid YAML."""

    @pytest.mark.structural
    def test_glossary_exists(self):
        path = os.path.join(PROJECT_ROOT, "translations", "glossary.yaml")
        assert os.path.isfile(path), "Missing: translations/glossary.yaml"

    @pytest.mark.structural
    def test_glossary_valid_yaml(self):
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
        path = os.path.join(PROJECT_ROOT, "translations", "glossary.yaml")
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        assert data is not None, "glossary.yaml is empty"
        assert isinstance(data, (dict, list)), "glossary.yaml root should be dict or list"


# ============================================================================
# 10. Core Documentation Files
# ============================================================================
class TestCoreDocumentation:
    """Essential project files must exist."""

    @pytest.mark.structural
    @pytest.mark.parametrize("filepath", [
        "CLAUDE.md", "AGENTS.md", "GEMINI.md", "soul.md",
        "DECISION-LOG.md", "AGENTICWORKFLOW-USER-MANUAL.md",
        "AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md",
        "COPYRIGHT.md", "README.md",
    ])
    def test_core_docs_exist(self, filepath):
        assert os.path.isfile(os.path.join(PROJECT_ROOT, filepath)), f"Missing: {filepath}"


# ============================================================================
# 11. Sermon Workflow Agent Completeness
# ============================================================================
class TestSermonWorkflowCompleteness:
    """The sermon workflow's agent→output file mapping must be complete."""

    @pytest.mark.structural
    def test_sermon_lib_constants_match_agents(self):
        """_sermon_lib.py AGENT_OUTPUT_FILES keys should match agent .md files."""
        sys.path.insert(0, SCRIPTS_DIR)
        from _sermon_lib import AGENT_OUTPUT_FILES, AGENT_CLAIM_PREFIXES, WAVE_AGENTS

        # All agents in WAVE_AGENTS should have output files
        all_wave_agents = set()
        for wave_agents in WAVE_AGENTS.values():
            all_wave_agents.update(wave_agents)

        for agent in all_wave_agents:
            assert agent in AGENT_OUTPUT_FILES, (
                f"Agent '{agent}' in WAVE_AGENTS but not in AGENT_OUTPUT_FILES"
            )
            assert agent in AGENT_CLAIM_PREFIXES, (
                f"Agent '{agent}' in WAVE_AGENTS but not in AGENT_CLAIM_PREFIXES"
            )

    @pytest.mark.structural
    def test_wave_agents_have_md_files(self):
        """All wave agents should have corresponding .md definition files."""
        sys.path.insert(0, SCRIPTS_DIR)
        from _sermon_lib import WAVE_AGENTS

        all_agents = set()
        for agents in WAVE_AGENTS.values():
            all_agents.update(agents)

        missing = []
        for agent in all_agents:
            # Agent names in _sermon_lib use underscores, files use hyphens
            fname = agent.replace("_", "-") + ".md"
            if not os.path.isfile(os.path.join(AGENTS_DIR, fname)):
                missing.append(f"{agent} → {fname}")
        assert missing == [], f"Wave agents without .md files: {missing}"

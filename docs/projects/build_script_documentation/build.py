#!/usr/bin/env python3
"""Interactive build menu for Company embedded firmware families."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
LOG_DIR = SCRIPT_DIR / "logs"
SUMMARY_HEADER = "\nBuild summary:"
HEARTBEAT_INTERVAL = 15
BUILD_VERSION_LINE_RE = re.compile(r'(set\s+Build_VersionNumber\s*=\s*")([^"\r\n]+)(")')
COMMON_VERSION_PATH = WORKSPACE_ROOT / "version" / "src" / "common_version.c"
# Tools driven from the command line (built in parallel); the rest run sequentially.
CLI_BUILD_TOOLS = frozenset({"build_tool 7.4", "build_tool 8.4"})
PROJECT_FILE_SUFFIXES = (".btp", ".btw", ".itp")
SCAN_PRUNE_DIR_NAMES = frozenset({".git", "Output", "Debug", "Release"})
BUILD_ALL_MENU_OPTION = "0"
BUILD_ALL_MODULES_OPTION = "1"
BUILD_CHERRY_PICK_OPTION = "2"
# Letter option in the main menu to wipe old builds/logs/temp files.
CLEAN_MENU_OPTION = "C"
# Rough per-project seconds for time estimates (build_tool vs ide_tool + populate overhead).
ESTIMATE_BUILD_TOOL_PROJECT_SEC = 120.0
ESTIMATE_IDE_TOOL_PROJECT_SEC = 300.0
ESTIMATE_POPULATE_SEC = 90.0

REQUIRED_FAMILY_FIELDS = {"code", "menu_option", "label", "projects"}
REQUIRED_PROJECT_FIELDS = {"name", "workspace", "project", "tool", "build_modes"}
MATURITY_BUILD_KEYS = ("SQA", "Field Trial", "Production")
BUILD_MODE_FIELDS = {"configuration", "artifact"}


class BuildException(RuntimeError):
    """Wrap build errors."""


@dataclass
class BuildModeEntry:
    configuration: str
    artifact: str


@dataclass
class ProjectRecord:
    name: str
    workspace: str
    project: str
    tool: str
    build_modes: Dict[str, BuildModeEntry]

    def build_target(self, maturity_label: str) -> BuildModeEntry:
        # Return configuration name and artifact path for SQA, Field Trial, or Production.
        # Raises if the project JSON has no build_modes entry for that maturity.

        if maturity_label not in self.build_modes:
            raise BuildException(
                f"[ERROR] Project '{self.name}' has no build_modes entry for "
                f"maturity '{maturity_label}'. "
                f"Expected one of: {', '.join(MATURITY_BUILD_KEYS)}"
            )
        return self.build_modes[maturity_label]


@dataclass
class FamilyRecord:
    menu_option: str
    label: str
    code: str
    bat_script: str | None
    projects: Tuple[ProjectRecord, ...]


@dataclass
class MaturityEntry:
    option: str
    label: str


@dataclass
class ToolInfo:
    env_var: str
    relative_exe: Path
    fallback_exe: Path


@dataclass
class BuildResult:
    name: str
    status: str
    duration: float
    log_path: Path | None


@dataclass
class FamilyAvailability:
    family_key: str
    label: str
    menu_option: str
    projects_ok: bool
    missing_projects: list[str]
    missing_tools: list[str]
    missing_script: bool

    @property
    def available(self) -> bool:
        return self.projects_ok and not self.missing_tools and not self.missing_script


@dataclass
class WorkspaceIndex:
    root: Path
    top_level_dirs: frozenset[str]
    dir_paths: frozenset[str]
    project_files: frozenset[str]


@dataclass
class AppConfig:
    families: Dict[str, FamilyRecord]
    maturities: Tuple[MaturityEntry, ...]
    tools: Dict[str, ToolInfo]


@dataclass
class MenuSelection:
    family_keys: list[str]
    maturity_label: str
    # None = build every project in the family; otherwise only these project names.
    cherry_pick_projects: frozenset[str] | None = None


@dataclass
class FamilyBuildOutcome:
    family_key: str
    label: str
    status: str
    duration: float
    estimated_duration: float
    error: str | None = None
    output_folder: Path | None = None


def tool_key(raw: str, tools: Dict[str, ToolInfo] | None = None) -> str:
    # Map a JSON tool string (e.g. "Build_tool 7.4") to a key in project_matrix tools.
    # Used at load time and during builds to pick build_tool vs ide_tool.

    catalog = tools if tools is not None else CONFIG.tools
    text = raw.strip().lower()
    if text in catalog:
        return text
    if text.startswith("build_tool 7.4"):
        return "build_tool 7.4"
    if text.startswith("build_tool 8.4"):
        return "build_tool 8.4"
    if "ide" in text:
        return "ide_tool"
    raise BuildException(f"Unknown tool: {raw}")


def _parse_build_modes(
    proj: dict, family_key: str, index: int, config_name: str
) -> Dict[str, BuildModeEntry]:
    # Read SQA / Field Trial / Production configuration and artifact paths from JSON.
    # Raises if any required maturity key or field is missing.

    label = f"Family '{family_key}', project #{index} in {config_name}"
    raw_modes = proj.get("build_modes")
    if raw_modes is None:
        raise BuildException(f"[ERROR] {label}: missing 'build_modes'.")

    if not isinstance(raw_modes, dict):
        raise BuildException(f"[ERROR] {label}: 'build_modes' must be an object.")

    modes: Dict[str, BuildModeEntry] = {}
    for maturity_key in MATURITY_BUILD_KEYS:
        if maturity_key not in raw_modes:
            raise BuildException(
                f"[ERROR] {label}: build_modes missing '{maturity_key}'."
            )
        entry = raw_modes[maturity_key]
        missing = BUILD_MODE_FIELDS - entry.keys()
        if missing:
            raise BuildException(
                f"[ERROR] {label}, build_modes['{maturity_key}'] missing: "
                f"{', '.join(sorted(missing))}"
            )
        modes[maturity_key] = BuildModeEntry(
            configuration=entry["configuration"],
            artifact=entry["artifact"],
        )
    return modes


def _norm_index_path(path: Path, root: Path) -> str:
    # Build a normalized relative path string for workspace index lookups.
    # On Windows, paths are casefolded so directory matching is case-insensitive.

    rel = path.relative_to(root).as_posix()
    if os.name == "nt":
        return rel.casefold()
    return rel


def load_config(path: Path) -> AppConfig:
    # Parse project_matrix.json into families, maturities, and tool definitions.
    # Validates required fields, build_modes per project, and unique menu options.

    if not path.exists():
        raise BuildException(
            f"[ERROR] Config file missing: {path}\n"
            f"       Create it or restore it from version control."
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildException(f"[ERROR] Invalid JSON in {path.name}: {exc}") from exc

    if not isinstance(raw, dict):
        raise BuildException(f"[ERROR] {path.name} must be a JSON object at the top level.")

    for section in ("maturities", "tools", "families"):
        if section not in raw:
            raise BuildException(f"[ERROR] {path.name} is missing '{section}' section.")

    json_maturity_keys = raw.get("maturity_build_keys")
    if json_maturity_keys is not None:
        if tuple(json_maturity_keys) != MATURITY_BUILD_KEYS:
            raise BuildException(
                f"[ERROR] {path.name} maturity_build_keys must be "
                f"{list(MATURITY_BUILD_KEYS)}."
            )

    maturities: list[MaturityEntry] = []
    for i, entry in enumerate(raw["maturities"]):
        for field in ("option", "label"):
            if field not in entry:
                raise BuildException(
                    f"[ERROR] maturities[{i}] in {path.name} missing '{field}'"
                )
        if entry["label"] not in MATURITY_BUILD_KEYS:
            raise BuildException(
                f"[ERROR] maturities[{i}] label '{entry['label']}' must be one of: "
                f"{', '.join(MATURITY_BUILD_KEYS)}"
            )
        maturities.append(MaturityEntry(
            option=str(entry["option"]),
            label=entry["label"],
        ))

    if {m.label for m in maturities} != set(MATURITY_BUILD_KEYS):
        raise BuildException(
            f"[ERROR] {path.name} maturities must define exactly: "
            f"{', '.join(MATURITY_BUILD_KEYS)}"
        )

    tools: Dict[str, ToolInfo] = {}
    for key, data in raw["tools"].items():
        for field in ("env_var", "relative_exe", "fallback_exe"):
            if field not in data:
                raise BuildException(
                    f"[ERROR] tools['{key}'] in {path.name} missing '{field}'"
                )
        tools[key] = ToolInfo(
            env_var=data["env_var"],
            relative_exe=Path(data["relative_exe"]),
            fallback_exe=Path(data["fallback_exe"]),
        )

    families: Dict[str, FamilyRecord] = {}
    for family_key, family_data in raw["families"].items():
        missing = REQUIRED_FAMILY_FIELDS - family_data.keys()
        if missing:
            raise BuildException(
                f"[ERROR] Family '{family_key}' in {path.name} missing fields: "
                f"{', '.join(sorted(missing))}"
            )
        if not isinstance(family_data["projects"], list):
            raise BuildException(
                f"[ERROR] Family '{family_key}' in {path.name}: 'projects' must be a list."
            )

        projects = []
        for i, proj in enumerate(family_data["projects"]):
            missing_proj = REQUIRED_PROJECT_FIELDS - proj.keys()
            if missing_proj:
                raise BuildException(
                    f"[ERROR] Family '{family_key}', project #{i} in {path.name} "
                    f"is missing fields: {', '.join(sorted(missing_proj))}"
                )
            build_modes = _parse_build_modes(proj, family_key, i, path.name)
            projects.append(ProjectRecord(
                name=proj["name"],
                workspace=proj["workspace"],
                project=proj["project"],
                tool=proj["tool"],
                build_modes=build_modes,
            ))

        for proj in projects:
            tool_key(proj.tool, tools)

        families[family_key] = FamilyRecord(
            menu_option=str(family_data["menu_option"]),
            label=family_data["label"],
            code=family_data["code"],
            bat_script=family_data.get("bat_script"),
            projects=tuple(projects),
        )

    menu_options = [f.menu_option for f in families.values()]
    if len(menu_options) != len(set(menu_options)):
        raise BuildException(
            f"[ERROR] Duplicate menu_option values in {path.name}; each family needs a unique option."
        )

    for family_key, family in families.items():
        if family.bat_script and not (SCRIPT_DIR / family.bat_script).is_file():
            print(
                f"[WARNING] Family '{family_key}': populate script not found: "
                f"{SCRIPT_DIR / family.bat_script}"
            )

    return AppConfig(
        families=families,
        maturities=tuple(maturities),
        tools=tools,
    )


def scan_workspace_index(root: Path) -> WorkspaceIndex:
    # Walk the workspace tree once and collect directory and project file paths.
    # Used at startup to check which JSON families can build on this machine.

    top_level: set[str] = set()
    dir_paths: set[str] = set()
    project_files: set[str] = set()

    if not root.is_dir():
        return WorkspaceIndex(
            root=root,
            top_level_dirs=frozenset(),
            dir_paths=frozenset(),
            project_files=frozenset(),
        )

    for entry in root.iterdir():
        if entry.is_dir():
            name = entry.name.casefold() if os.name == "nt" else entry.name
            top_level.add(name)

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SCAN_PRUNE_DIR_NAMES]
        current = Path(dirpath)
        try:
            dir_paths.add(_norm_index_path(current, root))
        except ValueError:
            continue
        for filename in filenames:
            if filename.lower().endswith(PROJECT_FILE_SUFFIXES):
                try:
                    project_files.add(_norm_index_path(current / filename, root))
                except ValueError:
                    pass

    return WorkspaceIndex(
        root=root,
        top_level_dirs=frozenset(top_level),
        dir_paths=frozenset(dir_paths),
        project_files=frozenset(project_files),
    )


CONFIG = load_config(SCRIPT_DIR / "project_matrix.json")
WORKSPACE_INDEX = scan_workspace_index(WORKSPACE_ROOT)


def resolve_matrix_path(raw: str, *, fallback_drive: str | None = None) -> Path:
    # Resolve a path from project_matrix.json relative to the Build folder.
    # Leading ../ reaches the workspace root; \\ paths use BUILD_WORKSPACE_ROOT if set.

    text = os.path.expandvars(raw.strip())
    text = text.strip("\"")
    text = text.replace("/", "\\")
    if not text:
        raise BuildException("Matrix path entry is blank")

    if text.startswith("\\\\"):
        return Path(text)

    drive = fallback_drive or SCRIPT_DIR.drive or Path.cwd().drive or "C:"

    if text.startswith("\\"):
        base_root_env = os.getenv("BUILD_WORKSPACE_ROOT")
        if base_root_env:
            guessed = Path(base_root_env) / text.lstrip("\\/")
            if guessed.exists():
                return guessed
        return Path(drive + text)

    path = Path(text)
    if path.is_absolute():
        return path

    return SCRIPT_DIR / path


def resolve_project_file(workspace: str, project: str) -> Path:
    # Resolve the IDE project file (.btp / .itp) from workspace and project strings.
    # Relative project names are resolved against the workspace directory.

    workspace_path = resolve_matrix_path(workspace)
    workspace_dir = workspace_path.parent
    project_path = Path(project.strip())
    if project_path.is_absolute() or project.strip().startswith("\\"):
        return resolve_matrix_path(project, fallback_drive=workspace_path.drive or None)
    return workspace_dir / project.strip()


def _path_in_index(absolute: Path, index: WorkspaceIndex) -> bool:
    # Return True if the path exists on disk and appears in the workspace index.
    # Falls back to exists() when the path is outside the indexed tree.

    if not absolute.exists():
        return False
    try:
        key = _norm_index_path(absolute, index.root)
    except ValueError:
        return absolute.exists()
    if absolute.is_dir():
        return key in index.dir_paths
    return key in index.project_files


def discover_families(
    index: WorkspaceIndex, config: AppConfig
) -> list[FamilyAvailability]:
    # For each JSON family, check workspace dirs, project files, tools, and populate script.
    # Returns availability flags used to mark menu entries as buildable or not.

    results: list[FamilyAvailability] = []

    for family_key, family in config.families.items():
        missing_projects: list[str] = []

        for project in family.projects:
            workspace_path = resolve_matrix_path(project.workspace)
            workspace_dir = workspace_path.parent
            dir_ok = _path_in_index(workspace_dir, index) or workspace_dir.exists()
            project_file = resolve_project_file(project.workspace, project.project)
            file_ok = _path_in_index(project_file, index) or project_file.is_file()

            if not dir_ok or not file_ok:
                missing_projects.append(project.name)

        missing_tools: list[str] = []
        for tool in sorted({p.tool for p in family.projects}):
            try:
                resolve_tool_path(tool)
            except BuildException:
                missing_tools.append(tool)

        missing_script = not family.bat_script or not (
            SCRIPT_DIR / family.bat_script
        ).is_file()

        results.append(FamilyAvailability(
            family_key=family_key,
            label=family.label,
            menu_option=family.menu_option,
            projects_ok=len(missing_projects) == 0,
            missing_projects=missing_projects,
            missing_tools=missing_tools,
            missing_script=missing_script,
        ))

    return results


def format_duration(seconds: float) -> str:
    # Convert seconds into a short human-readable string for logs and summaries.
    # Examples: 45s, 14m 32s, 1h 5m 0s.

    if seconds < 60:
        return f"{seconds:.0f}s"
    total_minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if total_minutes < 60:
        return f"{total_minutes}m {secs}s"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def family_log_dir(family_key: str) -> Path:
    # Return (and create) the log directory for one family under Build/logs/.
    # Keeps project and populate logs separate when building multiple families.

    path = LOG_DIR / family_key
    path.mkdir(parents=True, exist_ok=True)
    return path


def prompt_choice(valid_options: Iterable[str]) -> str:
    # Read stdin until the user enters one of the allowed menu option strings.
    # Exits the process on Ctrl+C.

    option_set = set(valid_options)
    while True:
        try:
            raw = input().strip()
        except KeyboardInterrupt:
            print("\n[ERROR] Input cancelled by user.")
            sys.exit(1)

        if raw in option_set:
            return raw

        print("[ERROR] Invalid option. Try again:", end=" ")


def _prompt_yes_no() -> bool:
    # Read stdin until the user types yes or no; used for clean confirmations.
    # Exits the process on Ctrl+C, like prompt_choice.

    while True:
        try:
            raw = input().strip().lower()
        except KeyboardInterrupt:
            print("\n[ERROR] Input cancelled by user.")
            sys.exit(1)
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("[ERROR] Please enter y or n:", end=" ")


def find_old_build_folders() -> list[Path]:
    # Find build output folders left in Build/ by previous runs.
    # Matches folder names like {CODE}_{Maturity}_{version} for known families.

    codes = sorted({fam.code for fam in CONFIG.families.values() if fam.code})
    if not codes:
        return []
    code_alt = "|".join(re.escape(c) for c in codes)
    maturity_alt = "|".join(re.escape(m) for m in MATURITY_BUILD_KEYS)
    pattern = re.compile(rf"^({code_alt})_({maturity_alt})_.+", re.IGNORECASE)
    folders = [
        entry
        for entry in SCRIPT_DIR.iterdir()
        if entry.is_dir() and pattern.match(entry.name)
    ]
    return sorted(folders)


def find_staged_temp_files() -> list[Path]:
    # Find leftover staged firmware files in Build/ (the *.hex copied for populate).
    # Leaves tools like hex_converter.exe alone since only *.hex are throwaway here.

    return sorted(p for p in SCRIPT_DIR.glob("*.hex") if p.is_file())


def run_clean_menu() -> None:
    # Sub-menu to delete old build folders, staged hex, and log files.
    # Lists what will be removed and always asks for confirmation first.

    print("\nWhat do you want to clean?\n")
    print("  1.- Old build output folders")
    print("  2.- Staged temp files (*.hex in Build/)")
    print("  3.- Log files (Build/logs)")
    print("  4.- All of the above")
    print("  0.- Back to main menu")
    print("\nChoice:", end=" ")
    choice = prompt_choice(["0", "1", "2", "3", "4"])
    if choice == "0":
        return

    targets: list[Path] = []
    if choice in ("1", "4"):
        targets.extend(find_old_build_folders())
    if choice in ("2", "4"):
        targets.extend(find_staged_temp_files())
    if choice in ("3", "4") and LOG_DIR.exists():
        targets.append(LOG_DIR)

    if not targets:
        print("[INFO] Nothing to clean.")
        return

    print("\n[INFO] The following items will be removed:")
    for path in targets:
        kind = "dir " if path.is_dir() else "file"
        print(f"  [{kind}] {path}")

    print(f"\nDelete these {len(targets)} item(s)? (y/n):", end=" ")
    if not _prompt_yes_no():
        print("[INFO] Clean cancelled.")
        return

    removed = 0
    for path in targets:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed += 1
        except OSError as exc:
            print(f"[ERROR] Could not remove {path}: {exc}")
    print(f"[INFO] Removed {removed} item(s).")


def interactive_menu() -> MenuSelection:
    # Show workspace summary, family menu (with availability), and maturity picker.
    # Returns selected family key(s) and maturity label (SQA, Field Trial, Production).

    print(
        f"[INFO] Workspace root: {WORKSPACE_INDEX.root} "
        f"({len(WORKSPACE_INDEX.top_level_dirs)} top-level folders, "
        f"{len(WORKSPACE_INDEX.dir_paths)} dirs indexed)"
    )

    availability = discover_families(WORKSPACE_INDEX, CONFIG)
    availability_by_key = {a.family_key: a for a in availability}
    families_sorted = sorted(
        CONFIG.families.items(),
        key=lambda item: int(item[1].menu_option),
    )

    available_keys = [a.family_key for a in availability if a.available]

    # Loop so the menu reappears after a clean instead of starting a build.
    while True:
        print("\nWhat software family are you trying to build?\n")
        if len(available_keys) > 1:
            print(
                f"{BUILD_ALL_MENU_OPTION}.- Build all available families "
                f"({len(available_keys)} families)"
            )
        for family_key, family in families_sorted:
            avail = availability_by_key[family_key]
            if avail.available:
                print(f"{family.menu_option}.- {family.label}")
            else:
                parts: list[str] = []
                if avail.missing_projects:
                    parts.append(f"missing projects: {', '.join(avail.missing_projects)}")
                if avail.missing_tools:
                    parts.append(f"missing tools: {', '.join(avail.missing_tools)}")
                if avail.missing_script:
                    family_rec = CONFIG.families[family_key]
                    if family_rec.bat_script:
                        parts.append(f"missing script: {family_rec.bat_script}")
                    else:
                        parts.append("missing script: not defined in JSON")
                print(f"{family.menu_option}.- {family.label}  [NOT AVAILABLE - {' | '.join(parts)}]")

        print(f"{CLEAN_MENU_OPTION}.- Clean old builds, temp files, and logs")

        valid_family_options = [a.menu_option for a in availability if a.available]
        if len(available_keys) > 1:
            valid_family_options = [BUILD_ALL_MENU_OPTION, *valid_family_options]
        # Clean is always offered, even when nothing can be built on this machine.
        valid_family_options.append(CLEAN_MENU_OPTION)
        if len(valid_family_options) == 1:
            print(
                "\n[WARNING] No software families are available to build on this machine.\n"
                "          Check workspace directories and build tools, or pick "
                f"{CLEAN_MENU_OPTION} to clean up."
            )

        print("\nSW:", end=" ")
        family_option = prompt_choice(valid_family_options)

        if family_option == CLEAN_MENU_OPTION:
            run_clean_menu()
            continue
        break

    if family_option == BUILD_ALL_MENU_OPTION:
        family_keys = sorted(
            available_keys,
            key=lambda key: int(CONFIG.families[key].menu_option),
        )
    else:
        family_keys = [
            key
            for key, fam in CONFIG.families.items()
            if fam.menu_option == family_option
        ]

    print("\nPick your build type/Maturity\n")
    for maturity in CONFIG.maturities:
        print(f"{maturity.option}.- {maturity.label}")
    print("  ")

    maturity_option = prompt_choice(m.option for m in CONFIG.maturities)
    maturity_label = next(
        m.label for m in CONFIG.maturities if m.option == maturity_option
    )
    if maturity_label not in MATURITY_BUILD_KEYS:
        print(f"[ERROR] Unknown maturity: {maturity_label}")
        sys.exit(1)

    cherry_pick_projects: frozenset[str] | None = None
    if len(family_keys) == 1:
        family = CONFIG.families[family_keys[0]]
        cherry_pick_projects = _prompt_module_selection(family, maturity_label)

    return MenuSelection(
        family_keys=family_keys,
        maturity_label=maturity_label,
        cherry_pick_projects=cherry_pick_projects,
    )


def _parse_module_number_list(text: str, max_index: int) -> set[int]:
    # Parse "1,3,5" or "1 3 5" into 1-based indices; empty means none selected yet.

    indices: set[int] = set()
    for part in re.split(r"[\s,;]+", text.strip()):
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"not a number: {part!r}")
        index = int(part)
        if index < 1 or index > max_index:
            raise ValueError(f"out of range (1-{max_index}): {index}")
        indices.add(index)
    return indices


def _prompt_module_selection(
    family: FamilyRecord, maturity_label: str
) -> frozenset[str] | None:
    # Ask whether to build all modules or a numbered subset for one family.
    # Returns None for all modules, or a set of project name strings to compile.

    print("\nWhich modules do you want to build?\n")
    print(f"  {BUILD_ALL_MODULES_OPTION}.- All modules")
    print(f"  {BUILD_CHERRY_PICK_OPTION}.- Cherry-pick modules (reuse existing .hex in Build/)")
    print("\nChoice:", end=" ")
    scope = prompt_choice([BUILD_ALL_MODULES_OPTION, BUILD_CHERRY_PICK_OPTION])
    if scope == BUILD_ALL_MODULES_OPTION:
        return None

    projects = list(family.projects)
    print("\nModules available for this family:\n")
    for index, project in enumerate(projects, start=1):
        target = project.build_target(maturity_label)
        hex_name = Path(target.artifact).name
        print(
            f"  {index}.- {project.name}  "
            f"[{target.configuration}] -> {hex_name}"
        )

    print(
        "\nEnter module numbers to build (e.g. 1,3,5). "
        "Unselected modules use existing .hex files in Build/ if present."
    )
    print("Numbers:", end=" ")
    while True:
        try:
            raw = input().strip()
        except KeyboardInterrupt:
            print("\n[ERROR] Input cancelled by user.")
            sys.exit(1)
        if not raw:
            print("[ERROR] Enter at least one module number. Numbers:", end=" ")
            continue
        try:
            picked = _parse_module_number_list(raw, len(projects))
        except ValueError as exc:
            print(f"[ERROR] {exc}. Numbers:", end=" ")
            continue
        if not picked:
            print("[ERROR] Enter at least one module number. Numbers:", end=" ")
            continue
        break

    names = frozenset(projects[i - 1].name for i in sorted(picked))
    skipped = [p.name for p in projects if p.name not in names]
    print(f"[INFO] Will build: {', '.join(sorted(names))}")
    if skipped:
        print(f"[INFO] Will reuse existing hex in Build/: {', '.join(skipped)}")
    return names


def estimate_family_duration(
    family: FamilyRecord, *, project_names: frozenset[str] | None = None
) -> float:
    # Estimate total build seconds for one family from project count and tool types.
    # Used for progress messages during build-all; values are rough constants.

    total = ESTIMATE_POPULATE_SEC
    for project in family.projects:
        if project_names is not None and project.name not in project_names:
            continue
        if tool_key(project.tool) in CLI_BUILD_TOOLS:
            total += ESTIMATE_BUILD_TOOL_PROJECT_SEC
        else:
            total += ESTIMATE_IDE_TOOL_PROJECT_SEC
    return total


def resolve_tool_path(tool_label: str) -> Path:
    # Find the compiler executable for a tool label using env vars or fallback paths.
    # Raises if the tool is unknown or the executable file is missing.

    key = tool_key(tool_label)
    info = CONFIG.tools[key]
    env_path = os.getenv(info.env_var)
    exe_path = Path(env_path) / info.relative_exe if env_path else info.fallback_exe
    if not exe_path.exists():
        raise BuildException(
            f"[ERROR] {key} missing. Set {info.env_var} or install at {exe_path}."
        )
    return exe_path


def ensure_path_exists(path: Path, message: str) -> None:
    # Raise BuildException with a clear message if the given path does not exist.
    # Shared guard for workspaces, projects, artifacts, and scripts.

    if not path.exists():
        raise BuildException(f"[ERROR] {message}: {path}")


def run_with_heartbeat(
    command: list[str], *, cwd: Path, log_path: Path, label: str
) -> int:
    # Run a subprocess, stream stdout to the log file, and print periodic status lines.
    # Returns the process exit code when the build command finishes.

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
        encoding="utf-8",
    )

    if process.stdout is None:
        process.wait()
        raise BuildException("[ERROR] Failed to capture build output stream")

    log_file = log_path.open("a", encoding="utf-8")

    def pump_output() -> None:
        # Copy subprocess stdout into the log file in a background thread.
        # Lets the main thread wait with heartbeat timeouts without blocking on I/O.

        try:
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
        finally:
            log_file.flush()

    reader = threading.Thread(target=pump_output, daemon=True)
    reader.start()

    try:
        while True:
            try:
                return_code = process.wait(timeout=HEARTBEAT_INTERVAL)
                break
            except subprocess.TimeoutExpired:
                print(f"[INFO] {label} still running...")
        reader.join()
    finally:
        if process.stdout:
            process.stdout.close()
        log_file.close()

    return return_code


def sync_build_version(family_code: str, populate_script_name: str) -> str:
    # Read {CODE}_BUILD_VERSION from common_version.c and write it into the populate .bat.
    # Returns the six-digit version string used for the output folder name.

    pattern = re.compile(
        rf"{re.escape(family_code)}_BUILD_VERSION\s*\{{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}}"
    )

    ensure_path_exists(COMMON_VERSION_PATH, "common_version.c missing")
    version_text = COMMON_VERSION_PATH.read_text(encoding="utf-8")
    match = pattern.search(version_text)
    if not match:
        raise BuildException(
            f"[ERROR] {family_code}_BUILD_VERSION not found in common_version.c"
        )

    major, minor, patch = (int(part) for part in match.groups())
    version_value = f"{major:02d}{minor:02d}{patch:02d}"

    populate_script_path = SCRIPT_DIR / populate_script_name
    ensure_path_exists(populate_script_path, f"{populate_script_name} missing")
    batch_text = populate_script_path.read_text(encoding="utf-8")
    replacement = BUILD_VERSION_LINE_RE.sub(
        lambda m: f"{m.group(1)}{version_value}{m.group(3)}",
        batch_text,
        count=1,
    )

    if replacement == batch_text:
        if not BUILD_VERSION_LINE_RE.search(batch_text):
            raise BuildException(
                f"[ERROR] Build_VersionNumber line not found in {populate_script_name}"
            )
    else:
        populate_script_path.write_text(replacement, encoding="utf-8")

    return version_value


def generate_changelog(family_code: str, maturity: str, version: str) -> str:
    # Build the text content for ChangeLog.txt in the family output folder.
    # Includes family, maturity, version, timestamp, and recent git commits if available.

    timestamp = datetime.now().strftime("%b %d, %Y %I:%M %p")

    git_log_lines: list[str] = []
    try:
        result = subprocess.run(
            ["git", "log", "-10", "--pretty=format:%h - %s [%an, %ad]", "--date=short"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=WORKSPACE_ROOT,
        )
        if result.returncode == 0 and result.stdout.strip():
            git_log_lines = result.stdout.strip().split("\n")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    lines = [
        "Build Information",
        "=" * 80,
        f"Family:    {family_code}",
        f"Maturity:  {maturity}",
        f"Version:   {version}",
        f"Build Date: {timestamp}",
        "",
        "Recent Changes",
        "=" * 80,
    ]

    if git_log_lines:
        lines.append("")
        lines.extend(f"  {line}" for line in git_log_lines)
    else:
        lines.extend(["", "  (Git log not available)"])

    lines.extend(["", f"Generated by build.py at {timestamp}", ""])
    return "\n".join(lines)


def build_project(
    record: ProjectRecord,
    target: BuildModeEntry,
    *,
    log_dir: Path | None = None,
) -> BuildResult:
    # Compile one matrix project with build_tool or ide_tool for the chosen configuration.
    # Copies the expected artifact hex into Build/ when the compiler succeeds.

    log_root = log_dir if log_dir is not None else LOG_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"{record.name}.log"
    start = time.perf_counter()

    workspace_path = resolve_matrix_path(record.workspace)
    workspace_dir = workspace_path.parent
    ensure_path_exists(workspace_dir, f"{record.name} workspace directory missing")

    project_path = resolve_project_file(record.workspace, record.project)
    ensure_path_exists(project_path, f"{record.name} project file missing")

    artifact_path = resolve_matrix_path(
        target.artifact,
        fallback_drive=workspace_path.drive or None,
    )

    tool_path = resolve_tool_path(record.tool)
    cwd = workspace_dir

    if tool_key(record.tool) in CLI_BUILD_TOOLS:
        command = [str(tool_path), str(project_path), "-build", target.configuration]
    else:
        ensure_path_exists(project_path, f"{record.name} project descriptor missing")
        project_dir = project_path.parent
        workspace_root = project_dir.parent if project_dir.parent else project_dir
        ensure_path_exists(project_dir, f"{record.name} project directory missing")
        ensure_path_exists(workspace_root, f"{record.name} workspace directory missing")
        project_name = project_dir.name
        command = [
            str(tool_path),
            "-nosplash",
            "--launcher.suppressErrors",
            "-no-indexer",
            "-verbose",
            "-application",
            "org.eclipse.cdt.managedbuilder.core.headlessbuild",
            "-data",
            str(workspace_root),
            "-removeAll",
            str(workspace_root),
            "-import",
            str(project_dir),
            "-cleanBuild",
            f"{project_name}/{target.configuration}",
        ]

    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"Command: {' '.join(command)}\n")
        log_file.flush()

    return_code = run_with_heartbeat(
        command, cwd=cwd, log_path=log_path, label=record.name
    )

    if return_code != 0:
        raise BuildException(
            f"[ERROR] {record.name} FAILED (exit {return_code}). See log: {log_path}"
        )

    ensure_path_exists(artifact_path, f"{record.name} artifact missing after build")
    shutil.copy2(artifact_path, SCRIPT_DIR / artifact_path.name)

    duration = time.perf_counter() - start
    print(f"[SUCCESS] {record.name} OK")
    return BuildResult(record.name, "OK", duration, log_path)


def stage_existing_hex(
    record: ProjectRecord,
    target: BuildModeEntry,
    *,
    log_dir: Path | None = None,
) -> BuildResult:
    # Skip compile and ensure the project hex is in Build/ for the populate script.
    # Uses Build/{hex} if present, otherwise copies from the workspace artifact path.

    start = time.perf_counter()
    hex_name = Path(target.artifact).name
    dest = SCRIPT_DIR / hex_name

    if dest.is_file():
        print(f"[INFO] {record.name}: using existing {hex_name} in Build/")
    else:
        workspace_path = resolve_matrix_path(record.workspace)
        artifact_path = resolve_matrix_path(
            target.artifact,
            fallback_drive=workspace_path.drive or None,
        )
        if artifact_path.is_file():
            shutil.copy2(artifact_path, dest)
            print(
                f"[INFO] {record.name}: copied {hex_name} from workspace "
                f"({artifact_path})"
            )
        else:
            raise BuildException(
                f"[ERROR] {record.name}: no hex for populate. "
                f"Expected {dest} or {artifact_path}"
            )

    log_root = log_dir if log_dir is not None else LOG_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"{record.name}.log"
    log_path.write_text(
        f"Skipped compile; staged existing hex: {dest}\n",
        encoding="utf-8",
    )
    duration = time.perf_counter() - start
    return BuildResult(record.name, "EXISTING", duration, log_path)


def run_population_script(
    script_name: str,
    output_folder: Path | None = None,
    *,
    log_dir: Path | None = None,
) -> BuildResult:
    # Run the family Populate_*.bat in the output folder to package hex files.
    # Disables "press any key" prompts and copies helper tools into the output dir.

    if not script_name:
        raise BuildException("[ERROR] Populate script not defined for this family")

    script_path = (SCRIPT_DIR / script_name).resolve()
    ensure_path_exists(script_path, "Populate script missing")

    work_dir = output_folder if output_folder else SCRIPT_DIR
    work_dir.mkdir(parents=True, exist_ok=True)
    output_script_path = work_dir / script_name

    script_content = script_path.read_text(encoding="utf-8")
    script_content = re.sub(
        r'^(set\s+/p\s+\w+\s*=.*PRESS ANY KEY.*)',
        r'REM \1',
        script_content,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    output_script_path.write_text(script_content, encoding="utf-8")

    if output_folder and output_folder != SCRIPT_DIR:
        for hex_file in SCRIPT_DIR.glob("*.hex"):
            if hex_file.is_file():
                shutil.copy2(hex_file, work_dir / hex_file.name)

    for tool_name in ("hex_converter.exe",):
        tool_src = SCRIPT_DIR / tool_name
        if tool_src.exists():
            shutil.copy2(tool_src, work_dir / tool_name)
        else:
            print(f"[WARNING] Tool {tool_name} not found, populate script may fail")

    log_root = log_dir if log_dir is not None else LOG_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"{script_path.stem}.log"
    start = time.perf_counter()

    with log_path.open("w", encoding="utf-8") as log_file:
        command = ["cmd.exe", "/c", str(output_script_path)]
        log_file.write(f"Command: {' '.join(command)}\n")
        log_file.write(f"Working directory: {work_dir}\n")
        log_file.flush()
        result = subprocess.run(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=work_dir,
            check=False,
        )

    if result.returncode != 0:
        raise BuildException(
            f"[ERROR] {script_path.name} FAILED (exit {result.returncode}). See log: {log_path}"
        )

    duration = time.perf_counter() - start
    print(f"[SUCCESS] {script_path.stem} OK")
    return BuildResult(script_path.stem, "OK", duration, log_path)


def build_family(
    family_key: str,
    maturity_label: str,
    *,
    cherry_pick_projects: frozenset[str] | None = None,
) -> FamilyBuildOutcome:
    # Build selected projects in a family, run populate, and write ChangeLog.txt.
    # cherry_pick_projects=None builds all; otherwise only listed names are compiled.

    if maturity_label not in MATURITY_BUILD_KEYS:
        msg = f"[ERROR] Unknown maturity: {maturity_label}"
        print(msg)
        return FamilyBuildOutcome(
            family_key=family_key,
            label=family_key,
            status="FAILED",
            duration=0.0,
            estimated_duration=0.0,
            error=msg,
        )

    total_start = time.perf_counter()
    family = CONFIG.families.get(family_key)
    label = family.label if family else family_key
    estimated = (
        estimate_family_duration(family, project_names=cherry_pick_projects)
        if family
        else 0.0
    )
    log_dir = family_log_dir(family_key)
    output_folder: Path | None = None
    build_project_names = (
        {p.name for p in family.projects}
        if cherry_pick_projects is None
        else set(cherry_pick_projects)
    )

    def _outcome(
        status: str, *, error: str | None = None, folder: Path | None = None
    ) -> FamilyBuildOutcome:
        # Build a FamilyBuildOutcome with elapsed time filled in for this family run.
        # Keeps early-return paths from duplicating outcome construction.

        return FamilyBuildOutcome(
            family_key=family_key,
            label=label,
            status=status,
            duration=time.perf_counter() - total_start,
            estimated_duration=estimated,
            error=error,
            output_folder=folder,
        )

    if family is None:
        msg = f"[ERROR] {family_key} data not found in config."
        print(msg)
        return _outcome("FAILED", error=msg)

    if not family.bat_script:
        msg = f"[ERROR] No populate script defined for {family_key}."
        print(msg)
        return _outcome("FAILED", error=msg)

    family_project_names = {p.name for p in family.projects}
    if cherry_pick_projects is not None:
        unknown = cherry_pick_projects - family_project_names
        if unknown:
            msg = f"[ERROR] Unknown module names for {family_key}: {', '.join(sorted(unknown))}"
            print(msg)
            return _outcome("FAILED", error=msg)
        if not cherry_pick_projects:
            msg = "[ERROR] Cherry-pick requires at least one module."
            print(msg)
            return _outcome("FAILED", error=msg)

    build_results: list[BuildResult] = []

    try:
        version_value = sync_build_version(family.code, family.bat_script)
        print(
            f"[INFO] Build version synced to {version_value} "
            f"from {family.code}_BUILD_VERSION."
        )

        if len(version_value) == 6:
            formatted_version = (
                f"{version_value[:2]}.{version_value[2:4]}.{version_value[4:]}"
            )
        else:
            formatted_version = version_value

        build_name = f"{family.code}_{maturity_label}_{formatted_version}"
        output_folder = SCRIPT_DIR / build_name

        module_note = (
            f"{len(build_project_names)}/{len(family.projects)} modules"
            if cherry_pick_projects is not None
            else f"{len(family.projects)} projects"
        )
        print(
            f"[INFO] Estimated build time: ~{format_duration(estimated)} "
            f"({module_note})"
        )
        print(f"[INFO] Creating output folder: {build_name}")
        print(f"[INFO] Logs: {log_dir}")

        project_results: Dict[str, BuildResult] = {}
        for project in family.projects:
            if project.name in build_project_names:
                continue
            project_results[project.name] = stage_existing_hex(
                project,
                project.build_target(maturity_label),
                log_dir=log_dir,
            )

        parallel_candidates = [
            p
            for p in family.projects
            if p.name in build_project_names and tool_key(p.tool) in CLI_BUILD_TOOLS
        ]
        sequential_candidates = [
            p
            for p in family.projects
            if p.name in build_project_names and p not in parallel_candidates
        ]

        def _run_project(project: ProjectRecord) -> BuildResult:
            # Build one project with the configuration/artifact for this maturity.
            # Called from the thread pool (build_tool) or the sequential loop (ide_tool).

            return build_project(
                project,
                project.build_target(maturity_label),
                log_dir=log_dir,
            )

        if parallel_candidates:
            max_workers = max(1, min(len(parallel_candidates), os.cpu_count() or 1))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(_run_project, project): project
                    for project in parallel_candidates
                }
                try:
                    for future in as_completed(future_map):
                        project = future_map[future]
                        try:
                            project_results[project.name] = future.result()
                        except BuildException as exc:
                            for pending in future_map:
                                pending.cancel()
                            raise exc
                        except Exception as exc:
                            for pending in future_map:
                                pending.cancel()
                            raise BuildException(
                                f"[ERROR] {project.name} failed with unexpected error: {exc}"
                            ) from exc
                except BaseException:
                    raise

        for project in sequential_candidates:
            project_results[project.name] = _run_project(project)

        build_results.extend(
            project_results[project.name] for project in family.projects
        )
        build_results.append(
            run_population_script(
                family.bat_script, output_folder, log_dir=log_dir
            )
        )

        print("[INFO] Cleaning up temporary files...")
        cleaned_count = 0
        for pattern in ("*.hex", "*.exe"):
            for temp_file in output_folder.glob(pattern):
                temp_file.unlink()
                cleaned_count += 1
        if cleaned_count > 0:
            print(f"[INFO] Removed {cleaned_count} temporary file(s) from output folder")

        print("[INFO] Generating ChangeLog.txt...")
        changelog_path = output_folder / "ChangeLog.txt"
        changelog_path.write_text(
            generate_changelog(family.code, maturity_label, formatted_version),
            encoding="utf-8",
        )
        print(f"[SUCCESS] ChangeLog.txt created in {build_name}")

    except BuildException as exc:
        print(exc)
        return _outcome("FAILED", error=str(exc), folder=output_folder)

    total_duration = time.perf_counter() - total_start
    print(SUMMARY_HEADER)
    for result in build_results:
        print(f"- {result.name}: {result.status} in {result.duration:.1f}s")
    print(f"Total: {total_duration:.1f}s (estimated ~{format_duration(estimated)})")
    print(f"\n[INFO] Build output available in: {output_folder}")
    return _outcome("OK", folder=output_folder)


def print_build_all_rollup(
    outcomes: list[FamilyBuildOutcome],
    maturity_label: str,
    total_elapsed: float,
) -> None:
    # Print the final build-all table: per-family status, times, and failures.
    # Shown after every family has been attempted (continue-on-error).

    succeeded = [o for o in outcomes if o.status == "OK"]
    failed = [o for o in outcomes if o.status != "OK"]
    total_estimated = sum(o.estimated_duration for o in outcomes)

    print("\n" + "=" * 72)
    print(f"Build-all summary ({maturity_label})")
    print("=" * 72)
    for outcome in outcomes:
        est = format_duration(outcome.estimated_duration)
        actual = format_duration(outcome.duration)
        line = f"  {outcome.family_key:<6} {outcome.status:<6} {actual:>10}  (est {est:>8})"
        if outcome.output_folder and outcome.status == "OK":
            line += f"  -> {outcome.output_folder.name}"
        print(line)
        if outcome.error:
            print(f"           {outcome.error}")
    print("-" * 72)
    print(
        f"  Total wall time: {format_duration(total_elapsed)} "
        f"(estimated ~{format_duration(total_estimated)})"
    )
    print(f"  Families: {len(succeeded)} succeeded, {len(failed)} failed, {len(outcomes)} total")
    if failed:
        print(f"  Failed: {', '.join(o.family_key for o in failed)}")
    print("=" * 72)


def build_all_families(family_keys: list[str], maturity_label: str) -> int:
    # Build each available family one after another for the same maturity.
    # Continues after failures and prints a rollup summary at the end.

    total_estimate = sum(
        estimate_family_duration(CONFIG.families[key]) for key in family_keys
    )
    print(
        f"\n[INFO] Build-all: {len(family_keys)} families, "
        f"estimated total ~{format_duration(total_estimate)}"
    )

    outcomes: list[FamilyBuildOutcome] = []
    overall_start = time.perf_counter()

    for index, family_key in enumerate(family_keys, start=1):
        family = CONFIG.families[family_key]
        family_estimate = estimate_family_duration(family)
        remaining_after = sum(
            estimate_family_duration(CONFIG.families[key])
            for key in family_keys[index:]
        )

        print("\n" + "=" * 72)
        print(
            f"[INFO] Family {index}/{len(family_keys)}: {family_key} - {family.label}"
        )
        print(
            f"[INFO] Estimated: ~{format_duration(family_estimate)} "
            f"({len(family.projects)} projects)"
        )
        if remaining_after > 0:
            print(
                f"[INFO] Remaining after this family: "
                f"~{format_duration(remaining_after)}"
            )

        outcome = build_family(family_key, maturity_label)
        outcomes.append(outcome)

        est = format_duration(outcome.estimated_duration)
        actual = format_duration(outcome.duration)
        if outcome.status == "OK":
            print(
                f"[INFO] {family_key} completed in {actual} "
                f"(estimated {est})"
            )
        else:
            print(
                f"[ERROR] {family_key} failed after {actual} "
                f"(estimated {est}); continuing with next family."
            )

    print_build_all_rollup(
        outcomes, maturity_label, time.perf_counter() - overall_start
    )
    return 0 if all(o.status == "OK" for o in outcomes) else 1


def main(argv: list[str]) -> int:
    # Entry point: interactive menu, then single-family or build-all for one maturity.
    # Exit code 0 only when every requested family build succeeds.

    if len(argv) > 1:
        print("[ERROR] CLI arguments not supported yet. Run without args for menu.")
        return 1

    selection = interactive_menu()
    if len(selection.family_keys) == 1:
        family_key = selection.family_keys[0]
        family = CONFIG.families[family_key]
        print(
            f"\n[INFO] Starting {family_key} - {family.label} "
            f"for {selection.maturity_label}."
        )
        if selection.cherry_pick_projects:
            print(
                f"[INFO] Cherry-pick modules: "
                f"{', '.join(sorted(selection.cherry_pick_projects))}"
            )
        outcome = build_family(
            family_key,
            selection.maturity_label,
            cherry_pick_projects=selection.cherry_pick_projects,
        )
        return 0 if outcome.status == "OK" else 1

    print(
        f"\n[INFO] Build-all selected: {len(selection.family_keys)} families "
        f"for {selection.maturity_label}."
    )
    return build_all_families(selection.family_keys, selection.maturity_label)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

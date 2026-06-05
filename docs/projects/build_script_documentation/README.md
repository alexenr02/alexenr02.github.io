# Firmware Build Orchestrator

Embedded firmware for multiple product families is often spread across several
IDE workspaces, each with its own toolchain (a command-line compiler for some
modules, an Eclipse-based IDE for others), its own build configurations
(SQA / Field Trial / Production), and a separate packaging step that stamps a
version number and bundles the resulting `.hex` files. Doing this by hand is
slow and error-prone: engineers open each project, pick the right configuration,
wait for the compile, copy artifacts, edit a version string in a `.bat` file, run
the packaging script, and assemble a release folder with a changelog. This script
replaces that whole sequence with a single interactive menu. It reads a JSON
matrix describing every family/project/tool, detects which families can build on
the current machine, compiles command-line projects in parallel while running
IDE projects sequentially, syncs the build version from `common_version.c`,
packages the output, and drops a timestamped release folder with a generated
`ChangeLog.txt`.

## Before vs After

| Old manual process (per release)                                              | Single-command equivalent                                  |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Open each module's project in `build_tool` / `ide_tool` one at a time         | Run `python build.py`                                      |
| Manually select the correct configuration (SQA / Field Trial / Production)    | Pick the maturity once from the menu                       |
| Trigger each compile and wait, watching for silent failures                   | Parallel command-line builds + live "still running" heartbeat |
| Hunt for each `.hex` artifact and copy it into the build folder               | Artifacts auto-copied into `Build/` on success             |
| Hand-edit `Build_VersionNumber` in the populate `.bat` file                   | Version auto-synced from `{CODE}_BUILD_VERSION` in `common_version.c` |
| Run the populate/packaging script and answer its prompts                      | Packaging script invoked automatically, prompts suppressed |
| Create the release folder named `{CODE}_{Maturity}_{version}` by hand         | Output folder created and named automatically              |
| Write the changelog and paste in recent commits                               | `ChangeLog.txt` generated with the last 10 git commits     |
| Repeat the entire flow for every product family                               | "Build all available families" option does them in sequence |
| Manually delete stale build folders, staged hex, and logs                     | Built-in `C` clean menu with confirmation                  |

## Usage

Run from the `Build/` directory that contains the script and `project_matrix.json`:

```bash
python build.py
```

The interactive flow:

1. **Pick a software family** (or `0` to build every available family). Families
   whose workspace, project files, or tools are missing on the current machine are
   shown as `[NOT AVAILABLE]` with the reason.
2. **Pick a maturity**: `SQA`, `Field Trial`, or `Production`. This selects the
   build configuration and the artifact path per project.
3. **Pick module scope** (single-family only):
   - All modules, or
   - Cherry-pick specific modules by number; unselected modules reuse the existing
     `.hex` already staged in `Build/`.

Output for each family lands in `Build/{CODE}_{Maturity}_{version}/` together with
a generated `ChangeLog.txt`. Per-project logs are written under `Build/logs/{family}/`.

### Cleaning up

Choose `C` from the main menu to remove old build folders, staged `*.hex` temp
files, and logs. Every delete is listed and confirmed before it runs.

### Repo contents

| File | Purpose |
| ---- | ------- |
| `build.py` | The orchestrator (run this). |
| `project_matrix.json` | Example matrix with two families (`ProductA`, `ProductB`) covering both tool types. |
| `Populate_ProductA.bat`, `Populate_ProductB.bat` | Example packaging scripts; show the `Build_VersionNumber` sync and prompt-suppression. |

The example matrix points at placeholder workspaces and tools that do not exist on a
clean checkout, so the menu shows both families as `[NOT AVAILABLE]` with the missing
pieces listed. That is expected: it demonstrates the availability detection. Point the
paths/tools at a real workspace (or set the tool env vars) to actually build.

### Configuration (`project_matrix.json`)

The script is data-driven; it does not hardcode families. The JSON defines:

- `maturities` - menu option/label pairs for `SQA`, `Field Trial`, `Production`.
- `tools` - per-tool `env_var`, `relative_exe`, and `fallback_exe` so the right
  compiler executable is located via environment variable or a default install path.
- `families` - each with a `menu_option`, `label`, `code`, optional populate
  `bat_script`, and a list of `projects`. Each project specifies its `workspace`,
  `project` file, `tool`, and a `build_modes` map giving the `configuration` and
  output `artifact` for every maturity.

### Environment variables

- Tool location env vars named in `project_matrix.json` (one per tool) point at the
  compiler install root.
- `BUILD_WORKSPACE_ROOT` (optional) resolves matrix paths that start with `\` when
  the default drive guess is not correct.

## Requirements

- **Python 3.10+** (uses `X | Y` type-union syntax and `frozenset[str]` generics).
- **Standard library only** - no third-party packages to install.
- **Windows** for the packaging step: the populate script is a `.bat` run via
  `cmd.exe`. The build/compile and menu logic are otherwise platform-independent.
- The build tools referenced in `project_matrix.json` must be installed (or their
  env vars set) for a family to be considered buildable.
- `git` on `PATH` is optional; it is only used to embed recent commits in the
  changelog and is skipped gracefully if unavailable.

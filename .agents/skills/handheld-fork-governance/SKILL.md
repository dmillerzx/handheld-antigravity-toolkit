---
name: handheld-fork-governance
description: >-
  Standardized runbook and governance protocols for maintaining downstream Android handheld ports
  (e.g., DKR-R, BanjoRecomp-Android). Covers continuous upstream sync, standalone APK preview packaging,
  CMake library target boundaries, CI host test flake isolation, AppStream metadata atomic sync,
  and upstream pull_request_target CI triage.
---

# Downstream Handheld Fork Governance & Release Skill

This skill provides operational workflows, CI triage protocols, and packaging procedures for maintaining downstream Android and handheld ports (`dmillerzx/*`) targeting the Retroid Pocket 5 (Qualcomm Snapdragon 865 / Adreno 650) running Android 13.

---

## 1. Governance Principles & Invariants

### A. Continuous Upstream Synchronization
- Maintain downstream branches (e.g., `main` on `dmillerzx/DKR-R`, `android` on `dmillerzx/BanjoRecomp-Android`) rebased against `upstream/main` and official release tags.
- Downstream branches must never lag behind upstream bugfixes and engine enhancements (`ahead_by: N, behind_by: 0`).
- Use fast-forward rebases or clean squashes rather than noisy merge bubbles.

### B. Community Standalone Release Obligation
- Handheld gaming users cannot compile C++ Android NDK projects on-device.
- Whenever upstream synchronization or a downstream platform fix completes, package standalone signed APKs (`Package-Android-Preview.ps1`) and publish them to GitHub Releases.
- Attach verified SHA-256 checksums and controller mapping instructions in the release notes.

### C. Android CMake Library Target Boundary
- Never invoke default or blanket build targets in hybrid C++/Android projects.
- Default targets frequently compile desktop host unit tests (e.g. `DKRMipmapLoadingTests`), which fail on Android toolchains due to native window type mismatches.
- Always build the specific Android shared library target (e.g., `DKRPortGame` / `libDKR-R.so` or `recomp_android`).

### D. CI Host Test Flake Isolation
- Host test failures on unrelated operating systems (e.g., WebRTC socket timeouts on macOS GitHub Actions runners) must be recognized as platform-specific CI flakes.
- Never let unrelated host test flakes block Android release delivery.

### E. Downstream Fork Branch Protection Prohibition
- Never configure GitHub branch protection rules or require mandatory passing status checks on downstream maintenance forks (`dmillerzx/*`).
- Upstream test flakes on unrelated OS targets block handheld Android PR merges, and branch protection obstructs zero-friction fast-forward rebasing against upstream release tags.

### F. Pattern-Guard Baseline Indexing & Transition-Layer PR Invariant (`PG013`)
- In repositories enforcing architectural pattern guards (e.g., `scripts/pattern_guard.py` rule `PG013`), newly staged dependency or platform patches must be sorted alphabetically into `architecture/pattern-guard-baseline.txt`.
- Accompanying pull requests must be explicitly tagged with the `transition-layer` label (`gh pr edit <PR> --add-label transition-layer`) so CI diff checks accept baseline expansion.

### G. Local Python Linter Preflight (`ruff`)
- Before pushing commits modifying Python contract tests, build tools, or packaging scripts in repos enforcing automated linting, always execute `ruff check` and `ruff format --check` locally to eliminate CI turnaround cycles.

### H. Homepage Release Prominence
- Standalone community APK releases must be promoted to the official latest release (`--latest`, `--prerelease=false`) so the download card and badge render prominently on the repository homepage sidebar rather than being collapsed under tags ("Create a new release").

---

## 2. Release Version & AppStream Metadata Atomic Synchronization Law (Law 16)

In projects enforcing release metadata validation (e.g., `DKR-R`), version increments must be atomically registered in Linux AppStream metadata.

### The Mechanism
`scripts/validate_release_metadata.py` (tested by `runtime-recomp/tests/build_tooling_tests.py` -> `ReleaseMetadataTests`) asserts that the version string in `VERSION` exists inside `packaging/linux/dkr-port.appdata.xml` under `<releases><release version="X.Y.Z" date="YYYY-MM-DD">`.

### Failure Mode
Bumping `VERSION` without updating `dkr-port.appdata.xml` causes `validate_release_metadata.py` to exit with code 1. This fails both `Repository Safety` and `Lint and static analysis` CI workflows on push.

### Required Synchronization Routine
Whenever updating `VERSION`:
1. Edit `packaging/linux/dkr-port.appdata.xml` and insert the new release block at the top of `<releases>`:
   ```xml
   <release version="1.0.14" date="2026-11-01">
       <description>
           <p>Summary of handheld optimizations and fixes.</p>
       </description>
   </release>
   ```
2. Run local hermetic validation:
   ```powershell
   python scripts/validate_release_metadata.py
   python scripts/check.py --suite tooling
   ```
3. Commit both files atomically.

---

## 3. Upstream `pull_request_target` Fork CI Triage Invariant (Law 17)

### The Mechanism
Upstream repositories that execute CI workflows triggered by the `pull_request_target` event (such as `AurelioB/BanjoRecomp-Android`'s `validate-external` workflow) run in the context of the base branch with access to repository secrets.

By default, GitHub's `actions/checkout@v4` action refuses to check out fork PR code in `pull_request_target` workflows unless the base workflow file contains `allow-unsafe-pr-checkout: true`.

### Failure Signature
```text
Refusing to check out fork pull request code from a 'pull_request_target' workflow.
Checkout of fork PRs must be explicitly permitted with 'allow-unsafe-pr-checkout: true'
or initiated by authorized repository collaborators.
```

### Operational Rule
- This failure is an **upstream repository security posture**, not an error, defect, or merge conflict in the fork PR.
- **Do not** attempt workarounds, commits, or force-pushes in the fork branch to "fix" upstream checkout rejections.
- Rely exclusively on autonomous fork workflows (`Android APK` on `dmillerzx/*`) to validate builds and tests.
- Document upstream triage status and await manual maintainer review.

---

## 4. Vulkan Mobile Scissor Rect & Viewport Clamping Invariant (`VUID-00282`)

On Qualcomm Adreno 650 (and all mobile Tile-Based Deferred Rendering GPUs):
- Negative scissor offsets (`left < 0` or `top < 0`) violate Vulkan specification `VUID-VkRect2D-offset-00282` and cause mobile hardware drivers to discard draw calls entirely.
- When rendering 2D HUDs, 3D viewports, or widescreen letterboxes, all scissor coordinates must be clamped strictly against target framebuffer boundaries (`[0, fbWidth]`, `[0, fbHeight]`) before calling `vkCmdSetScissor`.
- Zero-area or inverted rects must fall back to `VkRect2D{ {0, 0}, {0, 0} }`.

---

## 5. Platform-Agnostic Git Patch Streaming in Tests

When invoking `git apply` inside Python contract or unit tests across multiple host platforms:
- Never pass absolute Windows filesystem paths (`C:\...`) to `git apply <path>`, as MSYS/MinGW git misinterprets Windows drive prefixes.
- Always stream patch bytes via standard input:
  ```python
  subprocess.run(
      ["git", "-C", stage, "apply", "--recount", "--whitespace=error", "--ignore-space-change", "-"],
      input=patch_path.read_bytes(),
      check=True,
  )
  ```

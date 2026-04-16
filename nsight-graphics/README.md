# Nsight Graphics

This directory contains the CLI-Anything integration for **NVIDIA Nsight Graphics**.

It is designed for humans coordinating AI agents as well as for agents calling
the harness directly.

## What This Integration Does

- detects installed Nsight Graphics versions
- selects a specific install with `--nsight-path`
- launches a target or attaches to a running PID
- captures a frame
- collects a GPU Trace report
- summarizes exported GPU Trace timing results
- generates a C++ capture

## Recommended Human-to-AI Prompt Format

Give the AI these fields explicitly:

```text
Nsight version: 2026.1.0
Program: D:/path/to/YourApp.exe
Working dir: D:/path/to
Args: "D:\path\project.uproject" -dx12 -log -newconsole
Action: Graphics Capture / GPU Trace / C++ Capture
Trigger: after 10 seconds / frame 300 / I will press F11
Output: capture path / trace path / top 10 GPU hotspots / summary
```

## Prompt Examples

### Inspect installations

```text
Use the Nsight Graphics harness. List installed versions, tell me which one is selected, and switch to 2026.1.0 if available.
```

### One-step GPU Trace summary

```text
Use Nsight Graphics 2026.1.0 and run a GPU Trace on this executable.
Wait for me to press F11 manually.
After it finishes, give me:
- frame time
- estimated FPS
- draw count and dispatch count
- top 10 GPU events
- short diagnosis of what looks expensive
Program: D:/path/to/App.exe
Working dir: D:/path/to
Args: ...
```

### Automatic frame capture

```text
Launch this program under Nsight Graphics and automatically capture one frame after 10 seconds. Return the capture file path.
```

## Operator Notes

- If multiple Nsight versions are installed, pin one with `--nsight-path`
  when reproducibility matters.
- For one-step performance triage, prefer:

```bash
cli-anything-nsight-graphics gpu-trace capture --auto-export --summarize
```

- If a running process is already attached to a different Nsight activity,
  ask the AI to launch a fresh process for GPU Trace instead of reusing it.
- This harness is Windows-first and wraps the official CLI tools, not the full GUI.

## Related Docs

- Chinese guide: [README_CN.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\README_CN.md)
- Package usage: [agent-harness/cli_anything/nsight_graphics/README.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\cli_anything\nsight_graphics\README.md)
- Software notes: [agent-harness/NSIGHT_GRAPHICS.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\NSIGHT_GRAPHICS.md)
- Agent skill: [agent-harness/cli_anything/nsight_graphics/skills/SKILL.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\cli_anything\nsight_graphics\skills\SKILL.md)

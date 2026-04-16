# Nsight Graphics

这个目录包含 **NVIDIA Nsight Graphics** 的 CLI-Anything 集成。

它既面向直接调用 harness 的 AI，也面向“由人来调度 AI 使用这个能力”的工作流。

## 这个能力可以做什么

- 检测本机安装了哪些 Nsight Graphics 版本
- 用 `--nsight-path` 显式选择某个安装版本
- 启动目标程序或附加到已有 PID
- 抓取一帧图形捕获
- 收集一轮 GPU Trace
- 自动总结 GPU Trace 导出的耗时结果
- 生成 C++ Capture

## 推荐的人类提示格式

建议把这些信息明确告诉 AI：

```text
Nsight版本：2026.1.0
程序：D:/path/to/YourApp.exe
工作目录：D:/path/to
参数："D:\path\project.uproject" -dx12 -log -newconsole
动作：Graphics Capture / GPU Trace / C++ Capture
触发方式：10秒后 / 第300帧 / 我会按 F11
输出：capture 路径 / trace 路径 / Top10 GPU 热点 / 总结
```

## 提示示例

### 查看安装版本

```text
使用 Nsight Graphics harness，列出本机已安装版本，告诉我当前默认选中哪个，如果有 2026.1.0 就切过去。
```

### 一步式 GPU Trace 总结

```text
使用 Nsight Graphics 2026.1.0 对这个程序做一轮 GPU Trace。
等我手动按 F11 触发。
结束后给我：
- 帧时间
- 估算 FPS
- draw count 和 dispatch count
- 最耗时前 10 个 GPU 事件
- 一段简短诊断，说明主要瓶颈在哪里
程序：D:/path/to/App.exe
工作目录：D:/path/to
参数：...
```

### 自动抓帧

```text
用 Nsight Graphics 启动这个程序，10 秒后自动抓 1 帧，并把 capture 文件路径返回给我。
```

## 使用建议

- 多版本共存时，建议始终用 `--nsight-path` 固定版本。
- 如果你想让 AI 一步完成“抓 trace + 导出 + 总结”，优先让它使用：

```bash
cli-anything-nsight-graphics gpu-trace capture --auto-export --summarize
```

- 如果目标进程已经挂在其他 Nsight activity 上，建议让 AI 新起一个进程来跑 GPU Trace。
- 这个 harness 当前是 Windows-first，封装的是官方 CLI，不是完整 GUI 的全部功能。

## 相关文档

- 英文说明：[README.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\README.md)
- 包内使用说明：[agent-harness/cli_anything/nsight_graphics/README.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\cli_anything\nsight_graphics\README.md)
- 软件说明：[agent-harness/NSIGHT_GRAPHICS.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\NSIGHT_GRAPHICS.md)
- Agent 技能：[agent-harness/cli_anything/nsight_graphics/skills/SKILL.md](D:\code\D5\CLI-Anything-nsight-graphics-dev\nsight-graphics\agent-harness\cli_anything\nsight_graphics\skills\SKILL.md)

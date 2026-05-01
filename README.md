# SubAligner - 配音文案字幕生成器

一款**傻瓜式**的本地桌面应用，专为视频创作者设计。导入配音音频 + 粘贴配音文案，自动利用本地 AI 模型生成精确的 SRT 字幕文件。支持静音/气口检测与去除，一键导出干净配音 + 对应字幕，全程无需联网。

## 三步生成字幕

1. **拖入音频** — 支持 mp3/flac/wav/m4a
2. **粘贴文案** — 输入配音文稿
3. **一键生成** — AI 自动对齐生成 SRT（可选去静音）

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面框架 | Tauri 2 |
| 前端 | Vue 3 + TypeScript + Naive UI |
| AI 引擎 | Python FastAPI (Sidecar) |
| 强制对齐 | VAD (Silero) + wav2vec2 CTC |
| 静音检测 | Silero VAD |
| 音频处理 | ffmpeg |

## 开发环境搭建

### 前置依赖

- Node.js 20+
- Rust (via rustup)
- Python 3.11+
- ffmpeg

### 启动开发

```bash
# 安装前端依赖
npm install

# 构建 Python Sidecar（首次）
cd engine
pip install -r requirements.txt
pip install pyinstaller
python build.py
cd ..

# 启动 Tauri 开发模式
npm run tauri dev
```

### 仅启动前端（无 AI 引擎）

```bash
npm run dev
```

### 仅启动 Python 引擎

```bash
cd engine
pip install -r requirements.txt
python main.py --port 9580
```

## 项目结构

```
subaligner/
├── src/                    # Vue 前端
│   ├── views/              # 页面
│   ├── components/         # 组件
│   ├── composables/        # API 调用
│   ├── stores/             # Pinia 状态
│   └── utils/              # 工具函数
├── src-tauri/              # Tauri Rust 后端
│   ├── src/
│   ├── binaries/           # Python Sidecar 二进制
│   └── capabilities/
├── engine/                 # Python AI 引擎
│   ├── api/                # FastAPI 接口
│   ├── core/               # 核心算法
│   │   ├── aligner.py      # VAD + wav2vec2 强制对齐
│   │   ├── vad.py          # Silero VAD
│   │   ├── silence_remover.py  # 静音去除
│   │   ├── srt_remapper.py     # SRT 时间重映射
│   │   ├── audio_processor.py  # 音频预处理
│   │   ├── text_processor.py   # 文案预处理
│   │   └── srt_generator.py    # SRT 生成
│   └── models/             # 模型管理
└── .github/workflows/      # CI/CD
```

## 构建 & 发布

Mac 本地开发构建：

```bash
npm run tauri build
```

Windows 通过 GitHub Actions 构建（推送 tag 触发）：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 跨平台代码规范

- 路径：Python 用 `pathlib.Path`，TS 用 `path.join()`
- 换行：源码 LF，SRT 输出 CRLF
- Sidecar 通信：HTTP localhost（非 Unix Socket）
- 文件名：临时文件只用 ASCII
- 环境变量：用 Tauri `app.getPath()` API

## 许可证

MIT

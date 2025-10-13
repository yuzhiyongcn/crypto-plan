# UV 包管理器使用指南 ⚡️

本项目现在使用 [uv](https://github.com/astral-sh/uv) 作为推荐的包管理器。uv 是一个用 Rust 编写的超快 Python 包管理器，比 pip 快 10-100 倍！

## 🚀 为什么选择 uv？

- ⚡️ **极快速度**: 比 pip 快 10-100 倍
- 🔒 **可靠锁定**: 自动生成 `uv.lock` 确保依赖一致性
- 🎯 **统一工具**: 同时管理 Python 版本和依赖
- 💾 **全局缓存**: 避免重复下载包
- 🔄 **兼容性好**: 完全兼容 pip/PyPI 生态系统

## 📦 安装 uv

### Windows

```powershell
# 使用 PowerShell
irm https://astral.sh/uv/install.ps1 | iex
```

### Linux/macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 使用 pip

```bash
pip install uv
```

## 🎯 常用命令

### 初始化项目

```bash
# 同步依赖（首次运行或更新 pyproject.toml 后）
uv sync

# 同步包括开发依赖
uv sync --dev

# 仅安装主要依赖（不含开发依赖）
uv sync --no-dev
```

### 运行 Python 代码

```bash
# 运行 Python 脚本
uv run python src/crypto_data_fetcher.py

# 运行示例程序
uv run python examples/fetch_crypto_example.py

# 交互式 Python shell
uv run python

# 运行模块
uv run python -m src.crypto_data_fetcher
```

### 管理依赖

```bash
# 添加新依赖
uv add requests

# 添加开发依赖
uv add --dev pytest

# 添加指定版本
uv add "pandas>=2.1.0"

# 移除依赖
uv remove numpy

# 更新所有依赖
uv lock --upgrade

# 更新特定依赖
uv lock --upgrade-package requests
```

### 查看依赖

```bash
# 显示已安装的包
uv pip list

# 显示依赖树
uv pip tree

# 显示过时的包
uv pip list --outdated
```

## 📋 项目结构

```
虚拟货币投资计划/
├── pyproject.toml      # 项目配置和依赖定义
├── uv.lock            # 锁定的依赖版本（自动生成）
├── .python-version    # Python 版本指定
├── .venv/             # 虚拟环境（自动创建）
├── requirements.txt   # 传统 pip 兼容（可选）
└── src/               # 源代码
```

## 🔧 pyproject.toml 说明

我们的 `pyproject.toml` 包含：

```toml
[project]
name = "crypto-investment-tools"
version = "1.0.0"
requires-python = ">=3.9"

dependencies = [
    "ccxt>=4.1.0",
    "python-binance>=1.0.19",
    "requests>=2.31.0",
    "pandas>=2.1.0",
    "python-dotenv>=1.0.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

## 💡 实际使用示例

### 场景1: 首次克隆项目

```bash
# 1. 克隆项目
git clone <repository>
cd 虚拟货币投资计划

# 2. 安装依赖（自动创建虚拟环境）
uv sync

# 3. 运行项目
uv run python src/crypto_data_fetcher.py
```

### 场景2: 添加新功能需要新依赖

```bash
# 1. 添加依赖
uv add matplotlib

# 2. 依赖自动添加到 pyproject.toml 并更新 uv.lock

# 3. 使用新依赖
uv run python your_new_script.py
```

### 场景3: 开发环境设置

```bash
# 1. 安装包括开发依赖
uv sync --dev

# 2. 运行测试
uv run pytest

# 3. 格式化代码
uv run black src/

# 4. 代码检查
uv run ruff check src/
```

### 场景4: 更新依赖

```bash
# 1. 更新所有依赖到最新版本
uv lock --upgrade

# 2. 同步更新
uv sync

# 3. 测试是否正常工作
uv run python src/crypto_data_fetcher.py
```

## 🔄 从 pip 迁移到 uv

如果你之前使用 pip：

```bash
# 1. 删除旧的虚拟环境（可选）
rm -rf venv/

# 2. 使用 uv 同步依赖
uv sync

# 3. 后续使用 uv run 运行命令
uv run python src/crypto_data_fetcher.py

# 原来: python src/crypto_data_fetcher.py
# 现在: uv run python src/crypto_data_fetcher.py
```

## 🆚 uv vs pip 对比

| 功能 | uv | pip |
|------|-----|-----|
| 安装速度 | ⚡️ 超快 (10-100x) | 🐌 慢 |
| 依赖锁定 | ✅ `uv.lock` | ⚠️ 需手动维护 |
| 虚拟环境 | ✅ 自动管理 | ⚠️ 手动创建 |
| Python 版本管理 | ✅ 内置支持 | ❌ 需要 pyenv |
| 并行下载 | ✅ 是 | ❌ 否 |
| 全局缓存 | ✅ 是 | 部分支持 |
| 错误提示 | ✅ 清晰友好 | ⚠️ 一般 |

## 🔍 常见问题

### Q: uv 与 pip 的 requirements.txt 兼容吗？

**A**: 是的！我们保留了 `requirements.txt` 以便向后兼容：

```bash
# 从 requirements.txt 安装（使用 uv）
uv pip install -r requirements.txt

# 或使用传统 pip
pip install -r requirements.txt
```

### Q: 如何在 CI/CD 中使用 uv？

**A**: GitHub Actions 示例：

```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest
```

### Q: .venv 目录应该提交到 Git 吗？

**A**: 不应该！`.venv` 目录已在 `.gitignore` 中。只需提交：
- `pyproject.toml` (依赖定义)
- `uv.lock` (锁定版本)
- `.python-version` (Python 版本)

### Q: 如何指定 Python 版本？

**A**: 编辑 `.python-version` 文件：

```bash
# 使用 Python 3.12
echo "3.12" > .python-version

# uv 会自动使用指定版本
uv sync
```

### Q: 遇到依赖冲突怎么办？

**A**: uv 会给出清晰的错误提示：

```bash
# 查看详细信息
uv sync --verbose

# 尝试更新锁文件
uv lock --upgrade

# 如果仍有问题，手动调整 pyproject.toml 中的版本约束
```

## 📚 高级用法

### 工作区管理

```bash
# 激活虚拟环境（可选，通常不需要）
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 或者总是使用 uv run（推荐）
uv run python script.py
```

### 脚本依赖

在 Python 脚本中声明依赖：

```python
# /// script
# dependencies = ["requests", "pandas"]
# ///

import requests
import pandas as pd
```

然后运行：

```bash
uv run script.py  # uv 会自动安装依赖
```

### 环境变量

```bash
# 指定不同的 Python 版本
UV_PYTHON=python3.11 uv sync

# 使用系统 Python 而不是 uv 管理的
UV_SYSTEM_PYTHON=1 uv sync
```

## 🎓 学习资源

- [uv 官方文档](https://docs.astral.sh/uv/)
- [uv GitHub 仓库](https://github.com/astral-sh/uv)
- [Python 打包指南](https://packaging.python.org/)

## 💪 实用技巧

### 加速技巧

```bash
# 使用国内镜像（如需要）
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 或在 pyproject.toml 中配置
[[tool.uv.index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

### 一键命令别名（可选）

在 `.bashrc` 或 `.zshrc` 中添加：

```bash
# 简化命令
alias uvr='uv run python'
alias uvs='uv sync'
alias uva='uv add'

# 使用
uvr src/crypto_data_fetcher.py
```

### 项目模板

快速创建新项目：

```bash
# 创建新项目
uv init my-crypto-project
cd my-crypto-project

# 添加依赖
uv add ccxt pandas requests

# 开始编码
uv run python main.py
```

## 🎉 总结

使用 uv 的核心优势：

1. **更快**: 依赖安装速度提升 10-100 倍
2. **更可靠**: 自动锁定依赖版本
3. **更简单**: 一个命令搞定所有事
4. **更现代**: 完全支持 PEP 标准

从现在开始，所有新的依赖管理都推荐使用 uv！

---

**需要帮助？** 查看 [uv 文档](https://docs.astral.sh/uv/) 或在项目 issue 中提问。


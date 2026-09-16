# Shared Agent Configuration

使用 **chezmoi + 私有 GitHub 仓库**，在多台 Mac 之间同步公共 Agent 配置。

## 结构

- `~/.agents/`：公共配置和 Skills。
- `~/.agents/AGENTS.md`：所有 Agent 共用的唯一规则文件。
- Codex、Claude、Cursor、WorkBuddy 等 Agent 的 `AGENTS.md` 均链接到 `~/.agents/AGENTS.md`。

## 新 Mac 初始化

```bash
brew install chezmoi
chezmoi init git@github.com:laughmaker/agents-config.git
chezmoi apply
```

检查结果：

```bash
chezmoi doctor
chezmoi status
ls -l ~/.codex/AGENTS.md
```

## 日常同步

### 1. 开始工作前拉取更新

```bash
chezmoi update
```

### 2. 修改公共配置

直接编辑目标文件，例如：

```bash
vim ~/.agents/AGENTS.md
vim ~/.agents/skills/<skill-name>/SKILL.md
```

### 3. 将修改收回 chezmoi 仓库

```bash
chezmoi re-add ~/.agents
```

注意：`re-add` 只更新**已被管理**的文件，不会自动纳入新增的 skill 目录或文件。
新装或新建 skill 后必须显式添加，否则不会同步到其他 Mac：

```bash
chezmoi add ~/.agents/skills/<new-skill>
```

检查是否有遗漏（`chezmoi status` 不会提示未纳管的新文件）：

```bash
comm -13 <(chezmoi managed --include=files --path-style=absolute ~/.agents | sort) \
         <(find ~/.agents -type f ! -name ".DS_Store" | sort)
```

输出应为空；唯一预期项是 `~/.agents/backups/`（本地备份，按设计不纳入管理）。

### 4. 提交并推送

```bash
cd "$(chezmoi source-path)"
git status
git add .
git commit -m "Update agent config"
git push
```

### 5. 其他 Mac 获取更新

```bash
chezmoi update
```

## 简化流程

```text
一台 Mac 修改 ~/.agents
        ↓
chezmoi re-add ~/.agents
        ↓
git commit + git push
        ↓
其他 Mac 执行 chezmoi update
```

## 注意事项

- 修改前先执行 `chezmoi update` 拉取其他电脑的变更，减少 Git 冲突；但**若 `~/.agents` 已有尚未收回的改动，必须先 `chezmoi re-add`**，否则 `update` 会用源目录的旧版本覆盖本地修改。
- `~/.agents` 中不要保存 API Key、Token、会话记录、缓存或其他敏感数据。
- 各 skill 目录下的 `.last-update-check`（skill 更新检查缓存）与 `.DS_Store` 已由 `.chezmoiignore` 排除，不纳入同步。
- `~/.agents/AGENTS.md` 是公共规则的唯一来源，不要分别维护各 Agent 的副本。
- 新增 Agent 时，将它的规则文件链接到公共文件，然后用 `chezmoi add` 纳入管理：

```bash
mkdir -p ~/.new-agent
ln -sfn ~/.agents/AGENTS.md ~/.new-agent/AGENTS.md
chezmoi add ~/.new-agent/AGENTS.md
```

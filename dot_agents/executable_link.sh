mkdir -p ~/.codex ~/.claude ~/.cursor ~/.dsh ~/.minimax ~/.qoder-cn ~/.qwenworkcn ~/.workbuddy ~/.workbuddy/skills

ln -sfn ~/.agents/AGENTS.md ~/.codex/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.claude/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.cursor/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.dsh/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.minimax/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.qoder-cn/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.qwenworkcn/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.workbuddy/AGENTS.md

ln -sfn ~/.agents/skills/github-repo-cleanup ~/.workbuddy/skills/github-repo-cleanup
ln -sfn ~/.agents/skills/humanizer ~/.workbuddy/skills/humanizer
ln -sfn ~/.agents/skills/workbuddy-theme-authoring ~/.workbuddy/skills/workbuddy-theme-authoring
ln -sfn ~/.agents/skills/xiaohongshu-cli ~/.workbuddy/skills/xiaohongshu-cli


chezmoi add ~/.agents
chezmoi add ~/.codex/AGENTS.md
chezmoi add ~/.claude/AGENTS.md
chezmoi add ~/.cursor/AGENTS.md
chezmoi add ~/.dsh/AGENTS.md
chezmoi add ~/.minimax/AGENTS.md
chezmoi add ~/.qoder-cn/AGENTS.md
chezmoi add ~/.qwenworkcn/AGENTS.md
chezmoi add ~/.workbuddy/AGENTS.md
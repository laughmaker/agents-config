mkdir -p ~/.codex ~/.claude ~/.cursor ~/.dsh ~/.minimax ~/.qoder-cn ~/.qwenworkcn ~/.workbuddy 

ln -sfn ~/.agents/AGENTS.md ~/.codex/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.claude/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.cursor/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.dsh/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.minimax/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.qoder-cn/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.qwenworkcn/AGENTS.md
ln -sfn ~/.agents/AGENTS.md ~/.workbuddy/AGENTS.md


chezmoi add ~/.agents
chezmoi add ~/.codex/AGENTS.md
chezmoi add ~/.claude/AGENTS.md
chezmoi add ~/.cursor/AGENTS.md
chezmoi add ~/.dsh/AGENTS.md
chezmoi add ~/.minimax/AGENTS.md
chezmoi add ~/.qoder-cn/AGENTS.md
chezmoi add ~/.qwenworkcn/AGENTS.md
chezmoi add ~/.workbuddy/AGENTS.md
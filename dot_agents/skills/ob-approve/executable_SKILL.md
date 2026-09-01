---
name: ob-approve
description: 在用户确认后，将 pending_review 的 ingest 单元归档到 `00 AI/raw/processed`，并回补 wiki 中的 raw 引用。
---

# ob-approve
用于在用户确认无误后，将 `pending_review` 的 ingest 单元正式归档到 `00 AI/raw/processed/`。

## 执行步骤
1. 读取 `00 AI/AGENTS.md`，遵循其原则
2. 查看 `00 AI/raw/index.md` 与 `00 AI/wiki/log.md`
3. 扫描 `00 AI/raw/unprocessed/`
4. 找出状态为 `pending_review` 的 ingest 单元
5. 如果用户明确指定了某一组，就处理该组；否则优先处理最近一次进入 `pending_review` 的那一组
6. 核对对应 wiki 页面和 `processed_into` 字段是否存在
7. 记录该 ingest 单元内每个 raw 文件的旧路径与目标新路径
8. 对该 ingest 单元内的每个 raw 文件更新流程字段，例如：
   - `processing_status: processed`
   - `reviewed_at: <今天日期>`
   - `processed_at: <今天日期>`
9. 将该 ingest 单元内的 raw 文件迁移到 `00 AI/raw/processed/`
10. 同步修复对应来源页及其他 wiki 页面里引用这些 raw 的旧路径，至少包含：
    - frontmatter 中的 `raw_note`
    - 正文“来源信息”下的“原始资料”链接
    - 其他显式写死的 `raw/unprocessed/...` 路径字符串
11. 对本批 raw 做一次局部自检，确认 `00 AI/wiki/` 中不再残留这些旧路径
12. 更新 `00 AI/raw/index.md`
13. 在 `00 AI/wiki/log.md` 中追加一条 `approve` 日志

## 约束
- 只有在用户明确确认后，才允许执行本流程
- 本流程不应再大幅改写 wiki 正文
- 本流程允许且必须修复因 raw 迁移导致的路径引用问题
- 如果局部自检未通过，应明确列出残留旧路径，不能静默当作归档成功
- 如果发现 `pending_review` 组与现有 wiki 记录不一致，应先报告问题，不要强行归档

## 输出要求
- 先说明你将归档哪个 ingest 单元
- 完成后说明哪些 raw 文件已迁移到 `processed/`
- 明确说明本批 raw 的旧路径残留检查是否通过
- 如果因为校验失败而未归档，要明确指出原因

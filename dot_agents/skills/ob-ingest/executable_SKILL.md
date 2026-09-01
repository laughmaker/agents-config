---
name: ob-ingest
description: 处理 `00 AI/raw/unprocessed` 中的下一个 ingest 单元，更新 wiki，并将 raw 标记为 pending_review。
---

# ob-ingest
用于处理 `00 AI/raw/unprocessed/` 中的下一个 ingest 单元，并把结果整合进 wiki。

## 执行步骤
1. 读取 `00 AI/AGENTS.md`，遵循其原则
2. 查看 `00 AI/raw/index.md`、`00 AI/wiki/index.md` 与 `00 AI/wiki/log.md`
3. 扫描 `00 AI/raw/unprocessed/`
4. 根据以下优先级选择“下一个 ingest 单元”：
   - 同一子文件夹中的文件
   - 拥有相同 `ingest_group` 的文件
   - 否则选择单篇文件
5. 如果存在多个候选 ingest 单元，优先选择最早进入队列的那一组；如无法判断，则按名字典序选择第一组
6. 如果选中的是批次，确认它们确实主题相关；如批次明显过大，则拆成 2 到 5 篇的小批次
7. 提炼该来源或该批次来源的核心信息
8. 在 `00 AI/wiki/sources/` 中创建或更新对应的来源摘要页，并把它作为证据节点
9. 根据内容创建或更新相关的实体页、概念页、综合页
10. 为新增知识补充必要的 `[[双链]]`，关键结论优先链接到 `[[sources/...]]` 或 `[[sources/...#某小节]]`
11. 为核心页面维护 frontmatter 关系字段，例如 `supports`、`contradicts`、`related_entities`、`related_concepts`、`related_sources`
12. 更新 `00 AI/wiki/index.md`
13. 在 `00 AI/wiki/log.md` 中追加一条 `ingest` 日志
14. 对本次 ingest 单元内的每个 raw 文件分别更新流程字段，例如：
    - `processing_status: pending_review`
    - `reviewed_at:`
    - `processed_at:`
    - `processed_into: <对应来源页路径>`
15. 更新 `00 AI/raw/index.md`
16. 明确告诉用户这批 raw 已进入 `pending_review`，等待确认

## 约束
- `raw/` 中的正文默认只读
- 重要结论尽量附带来源页
- 优先让知识页链接到本地来源页，不要直接把外部 URL 当作主要图谱边
- 默认兼容 `wiki/concepts/`、`wiki/entities/`、`wiki/synthesis/` 下的用户自定义子文件夹
- 不确定内容要标记为“待确认”或“开放问题”
- 如果新来源与旧页面冲突，不要静默覆盖，要显式记录冲突
- 不要只生成一页摘要后就停止，应同步维护相关页面
- 只有在 `wiki/index.md`、`wiki/log.md`、`raw/index.md` 都更新成功后，才允许把 raw 状态改为 `pending_review`
- 默认一次只处理一个 ingest 单元；如果是批次，保持批次尽量小而相关
- 未经用户确认，不得把 raw 文件迁移到 `processed/`

## 空队列处理
如果 `00 AI/raw/unprocessed/` 为空：
- 明确说明当前没有待处理素材
- 不要创建空日志或空页面
- 直接停止

## 输出要求
- 先简述你选中了哪个 ingest 单元，以及你打算更新哪些页面
- 完成后简述新增和更新结果
- 明确说明哪些 raw 文件已进入 `pending_review`
- 如果发现资料不足或命名冲突，明确指出

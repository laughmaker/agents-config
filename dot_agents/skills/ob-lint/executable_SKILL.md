---
name: ob-lint
description: 对 `00 AI/wiki` 做结构、证据链、关系字段和 raw 状态一致性检查，并修复低风险问题。
---

# ob-lint
用于对整个 wiki 做一次结构和内容健康检查。

## 执行步骤
1. 读取 `00 AI/AGENTS.md`，遵循其原则
2. 查看 `00 AI/wiki/index.md`
3. 扫描 `00 AI/wiki/` 下各类页面
4. 识别以下问题：
   - 文档标题(h1,h2,h3,h4,h5,h6)：前面空行超过 1 行或者没有空行(意思是只能有 1 个空行)，后面有空行(意思是不能有空行)
   - 孤立页面
   - 缺少来源支撑的强结论
   - 被新资料推翻但未更新的旧结论
   - 高频提及但未独立建页的概念或实体
   - 重复页面或命名不一致
   - 交叉链接明显不足的页面
   - 知识页直接堆放外部 URL，而没有先落到本地来源页
   - 核心页面缺少 `supports`、`contradicts`、`related_*` 等关键关系字段
   - 只有 frontmatter 关系，没有正文双链支撑的页面
   - 来源页缺少 `raw_note` 或 `external_url`，导致证据链不完整
   - approve 后遗留的 `raw/unprocessed/` 旧路径字符串
   - 用户对 `concepts / entities / synthesis` 分类迁移后遗留的旧路径字符串或失效目录假设
   - `raw/index.md` 与 `raw/unprocessed/`、`raw/processed/` 实际状态不一致
   - 长时间停留在 `pending_review` 的 raw 素材
5. 对 `wiki/meta/` 中作为模板示例出现的路径字符串不要误报；优先检查真实来源页和知识页中的活跃残留
6. 给出一份按优先级排序的问题清单
7. 如有必要，直接修复低风险结构问题
8. 将 lint 结果追加到 `00 AI/wiki/log.md`

## 输出结构
- 发现的问题
- 已自动修复的内容
- 建议下一步处理的事项

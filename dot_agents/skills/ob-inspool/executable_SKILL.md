---
name: ob-inspool
description: 将一次高价值回答或阶段性结论回填为 `wiki` 页面，通常优先沉淀到 `00 AI/wiki/synthesis`。
---

# ob-inspool
用于把一次高价值回答沉淀回 wiki，而不是让它消失在聊天记录里。

## 适用场景
- 一个跨多个来源的比较分析
- 一个阶段性研究结论
- 一个值得长期保存的问答总结

## 执行步骤
1. 读取 `00 AI/AGENTS.md`，遵循其原则
2. 查看 `00 AI/wiki/index.md`
3. 判断这次内容最适合放入哪个目录，通常优先是 `00 AI/wiki/synthesis/`
4. 创建或更新对应页面
5. 为正文补充与现有页面的双链，关键结论优先链接到本地来源页
6. 补充或更新 frontmatter 中的 `supports`、`contradicts`、`related_*` 字段
7. 更新 `00 AI/wiki/index.md`
8. 在 `00 AI/wiki/log.md` 中追加一条 `query` 或 `refactor` 日志

## 写作要求
- 明确区分“事实依据”“综合结论”“推测或开放问题”
- 如果当前内容仍然证据不足，不要包装成“最终结论”
- 不要在正文中大量堆放外部 URL；优先把证据关系落到本地 `sources` 页面

---
name: xiaohongshu-market-research
description: "小红书品类调研：使用 redbook + xhs-cli 搜索关键词、分析话题热度、拆解爆款内容、提取竞品格局、分析评论区情感、生成结构化报告。当用户要求对某个品类/产品做小红书市场调研、竞品分析、内容策略时使用。"
---

# 小红书市场调研 Skill
对指定品类进行小红书市场调研，输出结构化报告。使用 `redbook`（`@lucasygu/redbook`）和 `xiaohongshu-cli` 作为数据采集工具。

## 工作流

### 步骤 0：前置检查
检查 `redbook whoami` 能否正常返回用户信息。如果无认证状态，按以下顺序尝试恢复：
1. 提示用户先在 Chrome 中登录 `xiaohongshu.com`
2. 运行 `redbook whoami` 重新检测
3. 若仍失败，运行 `pkill -f "Google Chrome" 2>/dev/null; sleep 2` 杀掉 Chrome 进程，再试 `redbook whoami`
4. 仍然不行则引导用户手动提供 Cookie 字符串

### 步骤 1：确定关键词体系
与用户确认核心品类关键词后，构建调研关键词体系：

| 类型 | 说明 | 示例（以猫毛过敏为例） |
|------|------|----------------------|
| 核心词 | 品类直接关键词 | "猫毛过敏" |
| 场景词 | 用户场景关键词 | "养猫过敏怎么办" |
| 产品词 | 已识别的品牌/产品关键词 | "洛卫家"、"冠能畅抚" |
| 竞品词 | 对比类关键词 | "冠能vs洛卫家" |
| 趋势词 | 最新趋势关键词 | "猫毛过敏 2026" |

### 步骤 2：话题热度分析
```bash
# 搜索话题标签曝光量
redbook topics "<核心词>"

# 拉取不同排序的笔记列表
redbook search "<核心词>" --sort popular --json 2>/dev/null
redbook search "<核心词>" --sort latest --json 2>/dev/null
redbook search "<核心词>" --sort general --json 2>/dev/null
```

提取维度：
- 核心话题及衍生话题的曝光量
- 话题关系链路，按以下表格格式输出：

| 阶段 | 话题 | 曝光量 | 说明 |
|------|------|--------|------|
| 认知层 | #核心话题 | xx万 | 品类认知入口 |
| 场景层 | #场景话题 | xx万 | 功能需求触发 |
| 方案层 | #方案话题 | xx万 | 决策搜索 |
| 产品层 | 品牌词 | — | 品牌检索 |

- 每日最新内容的主题和互动量趋势

### 步骤 3：内容生态分析
```bash
# 获取热门笔记
redbook search "<核心词>" --sort popular --json 2>/dev/null

# 提取爆款结构模板（传入2-3篇同类爆文URL）
redbook viral-template <url1> <url2> <url3> 2>/dev/null

# 分析单篇笔记
redbook analyze-viral <url> 2>/dev/null
redbook read <url> 2>/dev/null
```

分类笔记为三种模型，按以下表格提取：

| 模型 | 内容结构 | 数据特征 | 适用场景 |
|------|---------|---------|---------|
| 工具型干货攻略 | 长文（800-1100字），多品测评/横评 | 高收藏比（>60%） | 品牌内容 |
| 情感共鸣型 | 短内容+氛围感图片/视频 | 高分享率（>30%） | 品牌破圈 |
| 专业科普型 | 专家背书，科学原理解析 | 高收藏+高分享 | 建立信任 |

对每类提取结构公式、数据画像、评论区高频词。

### 步骤 4：竞品格局分析
```bash
# 逐一搜索已识别品牌/产品
redbook search "<品牌名>" --sort popular --json 2>/dev/null

# 查看品牌号内容
redbook search "<品牌名>" --sort latest --json 2>/dev/null
```

对每个竞品按以下表格整理：

| 品牌 | 定位 | 价格带 | 小红书声量 | 核心产品 | 运营现状 |
|------|------|--------|-----------|---------|---------|
| — | — | — | ★~★★★★★ | — | 官方号/KOL投放/站内闭环 |

### 步骤 5：产品方案提取
```bash
# 阅读高互动攻略类笔记全文
redbook read <url> 2>/dev/null

# 搜索特定产品/方案关键词
redbook search "<品类名> <产品形态>" --sort popular --json 2>/dev/null
```

提取用户方案链路，按以下格式输出：

| 路线 | 产品形态 | 价格区间 | 代表品牌/产品 |
|------|---------|---------|-------------|
| A：路线名 | — | — | — |
| B：路线名 | — | — | — |

路线对比：

| 维度 | A（路线名） | B（路线名） | C（路线名） |
|------|-----------|-----------|-----------|
| 客单价 | — | — | — |
| 决策门槛 | 低/中/高 | 低/中/高 | 低/中/高 |
| 复购潜力 | 高/中/低 | 高/中/低 | 高/中/低 |
| 小红书热度 | — | — | — |

### 步骤 6：评论区情感分析
```bash
# 从3-6篇头部笔记拉取评论
redbook comments <url> 2>/dev/null
```

对评论做分类分析：

| 类别 | 典型话题 | 情感取向 |
|------|---------|---------|
| 产品选购 | 购买渠道、品牌对比、效果疑问 | 理性比较 + 价格敏感 |
| 症状/需求描述 | 用户痛点、使用场景 | 用户画像 |
| 体验反馈 | 使用效果、复购意愿 | 高情感投入 |
| 品牌评价 | 吐槽、推荐、对比 | 信任/不信任 |

情感信号提取：恐惧驱动因素、情感绑定强度、广告敏感度、平替需求。

### 步骤 7：内容机会矩阵
基于上述分析，生成按优先级排列的内容机会：

| 优先级 | 机会内容 | 流量潜力 | 竞争强度 | 判断依据 |
|-------|---------|---------|---------|---------|
| P0 | — | ★★★★★ | ★ | 搜索流量大 + 用户决策需要 + 供给缺口 |
| P0 | — | ★★★★★ | ★★ | 同上 |
| P1 | — | ★★★★ | ★ | 增长趋势好 + 有供给但仍有机会 |
| P1 | — | ★★★★ | ★★★ | 同上 |
| P2 | — | ★★★ | ★★★★★ | 成熟赛道 + 需差异化 |
| P2 | — | ★★★ | ★★★★ | 同上 |

### 步骤 8：生成报告
按以下结构输出完整报告（markdown 格式）：

```
# <品类名> — 小红书市场调研完整报告

> 调研时间：<日期>
> 调研工具：redbook、xhs-cli

## 目录

1. 行业背景与市场规模（宏观数据+品类痛点+所处阶段）
2. 话题热度分析（核心曝光量+话题关系链路+时间趋势）
3. 内容生态与爆款拆解（三种模型+供给缺口）
4. 竞品格局（品牌矩阵+格局发现+运营现状）
5. 产品方案对比（方案链路+路线对比+用户消费）
6. 评论区情感分析（分类统计+情感信号）
7. 内容机会矩阵（优先级排序+产品机会）
8. 可执行策略建议（分阶段内容运营+KOL合作+产品策略）
9. 附录：品牌对比笔记框架（标题方案+正文结构+配图方案+预埋评论）
```

### 步骤 9：生成品牌对比笔记框架（可选）
如果用户需要，基于爆款拆解结果，生成可直接落地的小红书笔记框架：

| 模块 | 内容 |
|------|------|
| 标题方案 | 5个方向：数字式/问题式/结果式/悬念式/人群标签 |
| 正文结构 | 开篇共鸣→原理科普→核心对比→决策建议→CTA结尾 |
| 配图方案 | 8-10张图的内容规划（封面/产品/对比/场景/总结） |
| 预埋评论 | 5条预埋评论 + 对应回复策略 |
| 发布策略 | 最佳时段 + 标签策略 + 评论区运营节奏 |

## 工具安装
如果环境尚未安装工具：
```bash
# redbook
npm install -g @lucasygu/redbook

# xiaohongshu-cli
brew install pipx
pipx install xiaohongshu-cli

# 知识库（参考用）
git clone https://github.com/vivy-yi/xiaohongshu-skills.git ~/.agents/skills/xiaohongshu-skills
```

## 数据采集模板

### 搜索命令速查
| 用途 | 命令 |
|------|------|
| 话题标签 | `redbook topics "<keyword>" 2>/dev/null` |
| 热门搜索 | `redbook search "<keyword>" --sort popular --json 2>/dev/null` |
| 最新内容 | `redbook search "<keyword>" --sort latest --json 2>/dev/null` |
| 综合排序 | `redbook search "<keyword>" --sort general --json 2>/dev/null` |
| 翻页搜索 | `redbook search "<keyword>" --sort popular --page <N> --json 2>/dev/null` |
| 爆款模板 | `redbook viral-template <url1> <url2> 2>/dev/null` |
| 爆文分析 | `redbook analyze-viral <url> 2>/dev/null` |
| 全文阅读 | `redbook read <url> 2>/dev/null` |
| 拉评论 | `redbook comments <url> 2>/dev/null` |
| 用户分析 | `redbook user <userId> 2>/dev/null` |
| 用户笔记 | `redbook user-posts <userId> --json 2>/dev/null` |
| 交叉验证 | `xhs search "<keyword>" --sort popular --json 2>/dev/null` |

### JSON 解析模板
用于从 JSON 输出中提取结构化数据：

```python
python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', [])[:10]:
    try:
        n = item.get('note_card', item)
        tag = n.get('corner_tag_info', [{}])[0].get('text','?')
        print(f'[{tag}] ❤️ {n[\"interact_info\"][\"liked_count\"]:>6}  📌 {n[\"interact_info\"][\"collected_count\"]:>4}  💬 {n[\"interact_info\"][\"comment_count\"]:>3}  🔄 {n[\"interact_info\"][\"shared_count\"]:>3}  | {n.get(\"display_title\",\"?\")[:50]}')
        print(f'   👤 {n.get(\"user\",{}).get(\"nick_name\",\"?\")}')
    except:
        pass
"
```

### 输出报告注意事项
- 报告中所有竞品/产品评价需来自真实评论区，标注引用来源
- 互动数据（点赞/收藏/评论/分享）如实记录，不做估算
- 价格数据标注来源（笔记提及 vs 市场调研均价）
- 定义清楚每个"机会等级"的判断标准

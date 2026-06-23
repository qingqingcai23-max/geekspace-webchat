---
type: calculator-spec
system: daoist_arts
title: 道术与道教术数本地计算器规格
summary: 道术与道教术数从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 道术与道教术数本地计算器规格

## 计算范围

符箓、科仪、斋醮、内丹、雷法等资料结构化。

## 必需输入

- 事项类型
- 流派来源
- 文本或仪式描述

## 计算步骤

1. 来源分级
2. 科仪结构拆解
3. 禁忌检查
4. 象征解释
5. 安全与合法性审查

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 宗教实践不可自动化冒充
- 高风险内容只做文化解释

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

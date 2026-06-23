---
type: calculator-spec
system: onmyodo
title: 阴阳道本地计算器规格
summary: 阴阳道从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 阴阳道本地计算器规格

## 计算范围

阴阳五行、历法、方位禁忌、仪式语境。

## 必需输入

- 日期
- 方位或地点
- 事项类型

## 计算步骤

1. 历法换算
2. 方位禁忌检查
3. 五行阴阳映射
4. 仪式语境校验
5. 历史边界提示

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 历史制度和现代影视形象差异大

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

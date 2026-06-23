---
type: calculator-spec
system: name_studies
title: 姓名学本地计算器规格
summary: 姓名学从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 姓名学本地计算器规格

## 计算范围

姓名字义、音韵、五行、数理、文化语境。

## 必需输入

- 姓名或候选名
- 用途
- 出生信息可选

## 计算步骤

1. 拆字
2. 音义形审查
3. 数理计算
4. 五行归类
5. 文化风险过滤

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 笔画口径争议
- 不可夸大名字决定性

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

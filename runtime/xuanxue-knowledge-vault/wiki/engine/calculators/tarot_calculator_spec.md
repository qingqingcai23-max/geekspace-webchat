---
type: calculator-spec
system: tarot
title: 塔罗本地计算器规格
summary: 塔罗从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 塔罗本地计算器规格

## 计算范围

牌阵、牌位、牌义、正逆位、牌间关系。

## 必需输入

- 问题
- 牌阵
- 抽牌结果

## 计算步骤

1. 校验牌阵
2. 映射牌位
3. 解释单牌
4. 识别元素与数字关系
5. 综合牌间叙事

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 无抽牌结果时只能建议牌阵
- 不自动伪造随机牌

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

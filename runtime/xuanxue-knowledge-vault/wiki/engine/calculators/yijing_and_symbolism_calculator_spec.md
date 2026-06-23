---
type: calculator-spec
system: yijing_and_symbolism
title: 易经与象数本地计算器规格
summary: 易经与象数从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 易经与象数本地计算器规格

## 计算范围

起卦、卦爻、本互变错综、象数义理合参。

## 必需输入

- 问题
- 起卦方式
- 数字或时间
- 动爻

## 计算步骤

1. 校验起卦方式
2. 生成本卦
3. 确定动爻
4. 生成变卦
5. 生成互卦错卦综卦
6. 按问题类型取象

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 没有起卦数据时不得伪造卦象
- 义理和象数解释要分层

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

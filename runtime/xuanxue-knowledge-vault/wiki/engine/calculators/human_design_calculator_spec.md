---
type: calculator-spec
system: human_design
title: 人类图本地计算器规格
summary: 人类图从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 人类图本地计算器规格

## 计算范围

类型、策略、内在权威、中心、通道、轮回交叉。

## 必需输入

- 出生时间
- 出生地点

## 计算步骤

1. 星历换算
2. 人格/设计计算
3. 中心通道映射
4. 类型策略推导
5. 权威判断

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 依赖精确出生时间
- 现代综合体系来源争议

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

---
type: calculator-spec
system: kabbalah
title: 卡巴拉本地计算器规格
summary: 卡巴拉从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 卡巴拉本地计算器规格

## 计算范围

生命之树、十质点、路径、字母、对应关系。

## 必需输入

- 主题
- 质点或路径
- 文本来源

## 计算步骤

1. 定位质点路径
2. 查对应关系
3. 上下位结构分析
4. 跨体系映射
5. 输出象征层级

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 犹太语境和西方秘传语境必须区分

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

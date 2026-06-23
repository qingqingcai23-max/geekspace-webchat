---
type: calculator-spec
system: qizheng_siyu
title: 七政四余本地计算器规格
summary: 七政四余从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 七政四余本地计算器规格

## 计算范围

日月五星、四余、宫度、宫主、岁限。

## 必需输入

- 出生时间
- 出生地点
- 星历口径

## 计算步骤

1. 换算天体位置
2. 定宫度
3. 安七政四余
4. 判断宫主飞泊
5. 岁限引动

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 星历精度依赖外部天文库
- 古法和现代星历口径差异大

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

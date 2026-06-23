---
type: calculator-spec
system: vedic_astrology
title: 印度占星本地计算器规格
summary: 印度占星从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 印度占星本地计算器规格

## 计算范围

恒星黄道、星宿、分盘、Dasha、Yogas。

## 必需输入

- 出生时间
- 出生地点
- ayanamsa 口径

## 计算步骤

1. 星历换算
2. Rashi 排盘
3. Navamsa 分盘
4. 星宿定位
5. Dasha 阶段
6. Yogas 识别

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 需可靠星历库
- ayanamsa 差异影响结论

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

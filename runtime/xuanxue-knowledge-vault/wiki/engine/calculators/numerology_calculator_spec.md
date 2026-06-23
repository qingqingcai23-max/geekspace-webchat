---
type: calculator-spec
system: numerology
title: 数字命理本地计算器规格
summary: 数字命理从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 数字命理本地计算器规格

## 计算范围

生日数、路径数、姓名数字、周期数字。

## 必需输入

- 生日
- 姓名可选
- 采用体系

## 计算步骤

1. 提取生日数字
2. 计算生命路径数
3. 计算生日数
4. 计算个人年数
5. 姓名数字映射
6. 输出轻量象征

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 娱乐和象征参考为主
- 不可强决定性判断

## 实现状态

- 2026-06-07: 已在网页后端实现第一版本地数字命理计算器。
- 已实现：生命路径数、生日数、个人年数、拉丁字母姓名表达数。
- 暂未实现：中文姓名笔画口径、Chaldean 体系、多语言姓名归一化。
- API: `POST /api/calculate/numerology`

---
type: calculator-spec
system: physiognomy
title: 相术本地计算器规格
summary: 相术从输入到结构化输出的本地算法规格。
updated: 2026-06-07
---

# 相术本地计算器规格

## 计算范围

面相、手相、骨相、气色的观察记录与非决定性判断。

## 必需输入

- 图像或描述
- 年龄性别
- 观察场景

## 计算步骤

1. 分区记录
2. 形色纹痣分类
3. 三停五官映射
4. 动态状态标注
5. 输出非决定性参考

## 输出字段

- `raw_input`: 原始输入。
- `normalized_input`: 归一化输入。
- `derived_factors`: 派生结构。
- `question_mapping`: 与问题相关的对象。
- `judgement_candidates`: 候选判断。
- `missing_inputs`: 缺失输入。
- `risk_flags`: 争议、越界和降权原因。

## 降权与风险

- 涉及刻板印象风险
- 不可替代医学心理诊断

## 实现状态

- 已补齐本地计算器规格。
- 待实现具体算法或接入可靠领域库。

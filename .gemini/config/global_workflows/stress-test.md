---
name: stress-test
description: Audit agent-produced work across operating regimes with zero-regression fixes.
disable-model-invocation: true
---

Evaluate the target work directly within its active context immediately upon invocation. Output your evaluation in exactly **3 concise, direct sections** below without meta-commentary or bureaucratic fluff.

## 1. Reason for Existence

State precisely why this target element exists right where it is placed.

- **Problem Solved**: What exact problem, requirement, or intent does this specific element exist to solve or enforce right where it is placed?

## 2. Real-World Scenarios & Operating Regimes

Enumerate concrete, observable **real-world situations** that make this target necessary to exist, directly tied to its **Reason for Existence**. Strictly discard theoretical or AI-hallucinated edge cases.

Categorize how the target actually behaves under these real-world scenarios into three strict regimes:
- **Effective**: Real-world scenarios where the target works smoothly and efficiently as intended.
- **Degraded**: Real-world scenarios where the target still functions but does not perform as expected.
- **Dead**: Real-world scenarios where the target completely breaks down. State the exact scenario and reason for failure.

## 3. Zero-Regression Remediation

For every scenario categorized under **Degraded** and **Dead** above, propose a concise, actionable remediation strategy.

- **Alignment-Contract Clarity**: Pitch every proposal at the clarity level of an **Alignment Contract**, using terse, bulleted decisions to specify the exact mechanism, target boundary, and definitive choice.
- **Zero-Regression Guarantee**: Verify explicitly how every proposed fix strictly preserves all valid behaviors proven under the **Effective** regime in Section 2.

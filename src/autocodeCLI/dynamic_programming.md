# Dynamic Programming (DP) — Brief Overview

## What is Dynamic Programming?

**Dynamic Programming (DP)** is an algorithmic technique for solving complex problems by breaking them down into simpler **overlapping subproblems**, solving each subproblem **once**, and storing their solutions (memoization) to avoid redundant computation.

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Optimal Substructure** | An optimal solution to the problem contains optimal solutions to its subproblems. |
| **Overlapping Subproblems** | The same subproblems are solved repeatedly; DP stores results to avoid recomputation. |
| **Memoization (Top-Down)** | Recursive approach with caching (memoization) of subproblem results. |
| **Tabulation (Bottom-Up)** | Iterative approach that fills a table (usually an array/table) bottom-up. |

---

## When to Use DP

A problem is a good candidate for DP if it has:
1. **Overlapping subproblems** — same subproblems solved repeatedly
2. **Optimal substructure** — optimal solution builds from optimal sub-solutions

Common patterns:
- Optimization problems (min/max cost, max profit, shortest path)
- Counting problems (number of ways, number of sequences)
- Decision problems (can we achieve X?)

---

## Two Main Approaches

### 1. Top-Down (Memoization / Recursion + Cache)
```python
def fib(n, memo={}):
    if n <= 1: return n
    if n in memo: return memo[n]
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]
```

### 2. Bottom-Up (Tabulation / Iterative)
```python
def fib(n):
    if n <= 1: return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

| Aspect | Top-Down (Memoization) | Bottom-Up (Tabulation) |
|--------|------------------------|------------------------|
| Approach | Recursive + cache | Iterative + table |
| Space | O(n) call stack + cache | O(n) table (often optimizable to O(1)) |
| Stack overflow risk | Yes (deep recursion) | No |
| Code clarity | Often more intuitive | Sometimes more verbose |

---

## Classic DP Patterns

| Pattern | Example Problems |
|---------|------------------|
| **Fibonacci / Linear DP** | Fibonacci, Climbing Stairs, House Robber |
| **0/1 Knapsack** | 0/1 Knapsack, Subset Sum, Partition Equal Subset Sum |
| **Unbounded Knapsack** | Coin Change, Unbounded Knapsack, Rod Cutting |
| **Longest Common Subsequence (LCS)** | LCS, Edit Distance, Longest Palindromic Subsequence |
| **Longest Increasing Subsequence (LIS)** | LIS, Russian Doll Envelopes |
| **Interval DP** | Matrix Chain Multiplication, Burst Balloons |
| **Tree DP** | House Robber III, Binary Tree Max Path Sum |
| **DP on Strings** | Edit Distance, Distinct Subsequences |
| **DP on Grids** | Unique Paths, Minimum Path Sum, Dungeon Game |
| **Bitmask DP** | Traveling Salesman, Assignment Problem |

---

## Time & Space Complexity

| Approach | Time | Space |
|----------|------|-------|
| Naive Recursion | O(2ⁿ) | O(n) call stack |
| Memoization | O(n) subproblems × O(1) each = O(n) | O(n) cache + O(n) stack |
| Tabulation | O(n) | O(n) (often optimizable to O(1)) |

---

## Common DP Patterns Cheatsheet

| Problem Type | State Definition | Transition |
|--------------|------------------|------------|
| Fibonacci | `dp[i] = max profit up to i` | `dp[i] = dp[i-1] + dp[i-2]` |
| 0/1 Knapsack | `dp[i][w] = max value using first i items with weight w` | `dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt[i]] + val[i])` |
| LCS | `dp[i][j] = LCS of s1[:i] and s2[:j]` | `dp[i][j] = dp[i-1][j-1]+1 if match else max(dp[i-1][j], dp[i][j-1])` |
| LIS | `dp[i] = LIS ending at i` | `dp[i] = max(dp[j]+1) for j<i and arr[j]<arr[i]` |
| Edit Distance | `dp[i][j] = edit dist between s1[:i] and s2[:j]` | `min(insert, delete, replace)` |

---

## Space Optimization Tricks

| Pattern | Optimization |
|---------|--------------|
| Fibonacci / Linear DP | Keep only last 2 values → **O(1) space** |
| 0/1 Knapsack | Iterate weight **backwards** → **O(W) space** |
| LCS / Edit Distance | Keep only **2 rows** → **O(min(m,n)) space** |
| LIS | Use **binary search + tails array** → **O(n log n) time, O(n) space** |

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Forgetting base cases | Always define `dp[0]`, `dp[1]`, or `dp[0][*]` / `dp[*][0]` |
| Off-by-one errors | Be careful with 0-index vs 1-index in DP tables |
| Not handling overlapping subproblems | Use memoization or tabulation |
| Stack overflow in deep recursion | Use bottom-up tabulation or increase recursion limit |
| Over-optimizing space too early | Get correct O(n²) solution first, then optimize |

---

## Classic Problems to Practice

| Difficulty | Problems |
|------------|----------|
| **Easy** | Climbing Stairs, House Robber, Fibonacci, Min Cost Climbing Stairs |
| **Medium** | Coin Change, Longest Increasing Subsequence, Edit Distance, Unique Paths, House Robber II, Coin Change 2 |
| **Hard** | Edit Distance, Burst Balloons, Regular Expression Matching, Distinct Subsequences, Palindrome Partitioning II |

---

## Quick Decision Guide: "Is this DP?"

1. **Can the problem be broken into subproblems?** → Yes → Continue
2. **Do subproblems overlap?** → Yes → DP is likely a good fit
3. **Does optimal solution use optimal sub-solutions?** → Yes → Optimal substructure ✓
4. **Can you define a state and transition?** → Yes → Define `dp[i]` or `dp[i][j]` and recurrence

---

## Quick Reference: Top-Down vs Bottom-Up Template

```python
# Top-Down (Memoization)
def dp(i, j):
    if base_case: return base_value
    if (i, j) in memo: return memo[(i, j)]
    ans = recurrence(dp(i-1, j), dp(i, j-1), ...)
    memo[(i, j)] = ans
    return ans

# Bottom-Up (Tabulation)
dp = [[0] * (n+1) for _ in range(m+1)]
for i in range(1, m+1):
    for j in range(1, n+1):
        dp[i][j] = recurrence(dp[i-1][j], dp[i][j-1], ...)
return dp[m][n]
```

---

## Summary

> **Dynamic Programming = Recursion + Memoization = Optimal Substructure + Overlapping Subproblems**

| Step | Action |
|------|--------|
| 1 | Identify if problem has optimal substructure & overlapping subproblems |
| 2 | Define state (`dp[i]` or `dp[i][j]`) — what does it represent? |
| 3 | Define base cases |
| 4 | Define recurrence relation (transition) |
| 5 | Choose top-down (memo) or bottom-up (tabulation) |
| 6 | Optimize space if possible |

---

*Keep practicing classic patterns — DP becomes intuitive with pattern recognition!*
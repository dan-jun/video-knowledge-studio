# Source selection and learning-pack workflow

## Source rubric

Prefer sources that score well on all of these:

| Dimension | What to check |
| --- | --- |
| Relevance | Directly covers the requested concept and project context |
| Correctness | Concrete examples, definitions and claims are internally consistent |
| Complementarity | Adds an explanation, derivation, demonstration or counterexample the others lack |
| Evidence | Provides code, source material, timestamps or reproducible examples |
| Accessibility | Captions/transcript are available and the media can be processed lawfully |
| Independence | Multiple selected sources do not merely repeat the same creator or script |

Record rejected sources and the reason. A source can be technically popular but still be
a poor fit because it is off-topic, too advanced, duplicated, inaccessible or uncited.

## Learning brief

Use this shape:

```text
目标：完成后能够做什么
当前基础：已经知道什么，卡在哪里
时间预算：总时长与每天可投入时间
项目上下文：为什么现在需要这块知识
成功标准：能解释、能推导、能实现、能判断或能应用
范围边界：本次不学什么
```

For fragmented learning, prefer a sequence of 2-6 minute `scipop` modules over forcing a
single long course. Each module should answer one learner question and end with a recall
check. For a coherent 15–60 minute curriculum, use `course` with chapters and exercises.
Use `remix` only when one source is the intended canonical source and information
preservation matters.

## Source ledger

For every candidate, keep:

```json
{
  "id": "S1",
  "platform": "bilibili",
  "url": "https://...",
  "title": "...",
  "author": "...",
  "duration": "12:34",
  "language": "zh-CN",
  "captions": true,
  "concepts": ["..."],
  "reason_selected": "...",
  "limitations": "..."
}
```

The production `course` validator requires at least two registered sources. Its citation
format is `S# p## mm:ss`; keep the source IDs in the ledger aligned with the spec.

## Notes and integration

Do not paste source summaries serially. Reorganize around the learner's goal:

1. define terms before using them;
2. establish prerequisites and a concept dependency graph;
3. explain mechanisms with a visual or concrete example;
4. preserve source-backed evidence and timestamps;
5. compare conflicting explanations and state the uncertainty;
6. add exercises, answers and a final recall page;
7. finish with a compact synthesis that connects the new concept to the project need.

## Verification

A delivery is incomplete unless:

- selected URLs and source metadata are real;
- the final MP4 exists and is playable;
- mode gates pass or every remaining failure is reported;
- note timestamps seek to the intended video positions;
- the course pack loads in Video Knowledge Studio;
- at least one representative frame has been inspected for text overlap and missing
  content;
- the learner can find the cited source behind each major conclusion.

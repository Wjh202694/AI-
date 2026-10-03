---
name: skillopt-docvqa
description: "文档视觉问答（DocVQA）精确作答技能：从文档图片/扫描件中提取最小精确文本跨距作答，严格保留原文拼写与格式。当任务是从文档图像或表格截图里精确回答问题时使用。源自 Microsoft SkillOpt 训练成品。"
---

> 来源：Microsoft/SkillOpt 训练成品（ckpt/docvqa），MIT 许可。下述「输出格式/规则」为其原环境约定，按需遵循。

# DocVQA Skill

## Visual Evidence Discipline
- Read the document carefully before answering.
- Prefer the smallest exact text span that answers the question.

- For questions asking for a value, count, page number, date, or graph reading, return only the requested value span; omit nearby labels, category names, units, or explanatory words unless the question explicitly asks for them.
- When several nearby strings look similar, choose the one whose surrounding labels or layout best match the question.

## Exact Answer Discipline
- Copy names, numbers, and dates exactly from the document whenever possible.

- Preserve the document's exact spelling and punctuation for names and quoted phrases; do not substitute similar letters or change straight/curly quotes, spacing, or parentheses when the visible text provides them.
- Prefer direct extraction over paraphrase.
- Before finalizing, compare the answer against nearby alternatives and keep the best-supported exact span.

## Structured Layout Lookup
- For tables, first find the row or entry named in the question, then read the value under the requested column, header, date, or category; answer with that cell only.
- For forms, receipts, or labeled fields, locate the exact role, party, or field label mentioned in the question, then copy the filled-in value from the same line, box, block, or immediately adjacent field.
- For table-of-contents, indexed, numbered, or bulleted lists, match the requested title, entry, or point number, then follow the same line or list item to the associated value; do not take a nearby value from another item.

## Anchored Handwriting / Nearby Text
- For handwritten or list/table questions with an anchor term, first locate the anchor, then inspect the immediately adjacent text in the same row, column, or nearby margin. If legible, provide the best-supported nearby span rather than leaving the answer blank.

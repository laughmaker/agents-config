---
name: xhs-upload-kol-to-lark
description: Update a Feishu/Lark Base KOL table from local Excel files. Use when the user wants to import or update Xiaohongshu/Pugongying influencer contact information into a Feishu Base, deduplicating by 达人昵称 and writing only 达人昵称、手机号、微信号、达人蒲公英地址.
---

# XHS Upload KOL To Lark

## Purpose

Update a Feishu/Lark Base table from one or more local `.xlsx` files containing KOL/blogger information. Deduplicate by `达人昵称`, update existing Base records with the same nickname, and create records for new nicknames.

## Required companion skills

Before touching Feishu/Lark, load and follow:

- `lark-base`
- `lark-shared`

Use `lark-cli base +...` commands only; do not switch to raw OpenAPI unless `lark-base` explicitly routes there.

## Fixed data contract

Only read and write these fields:

- `达人昵称`
- `手机号`
- `微信号`
- `达人蒲公英地址`

Ignore all other Excel columns and Base fields.

Use `达人昵称` as the business key. Trim whitespace. Do not match by row number, URL, phone, WeChat, or visual order.

## Workflow

1. Parse the user-provided Excel files.
   - Confirm all four required columns exist.
   - Read every row with a non-empty `达人昵称`.
   - Merge duplicate nicknames inside the Excel inputs.
   - Prefer non-empty values.
   - If two non-empty values conflict for the same nickname and field, stop and show the conflict; do not write.
2. Resolve the target Feishu link.
   - If the URL is a Wiki URL, use `lark-cli wiki spaces get_node` to resolve `obj_token`.
   - Confirm `obj_type` is `bitable`.
   - Treat the resolved `obj_token` as the actual Base token. Do not use the Wiki node token as `--base-token`.
   - Use the URL `table=...` parameter as the table ID when present.
3. Read Base field structure.
   - Confirm the four target fields exist.
   - Confirm they are writable storage fields, not formula/lookup/system fields.
   - Note field types. In this user’s table, `手机号` may be a `number`; if so, write pure digit phones as JSON numbers and stop on non-digit phone values.
4. Read existing Base records with a minimal projection:
   - `达人昵称`
   - `手机号`
   - `微信号`
   - `达人蒲公英地址`
   - retain `record_id`.
   - Page through all records if `has_more` is true.
5. Build an index by `达人昵称`.
   - If the Base already contains duplicate nicknames, stop and report the duplicate records; do not write because update target is ambiguous.
6. Do a dry-run summary before writing when the user has not already approved writes in the current turn:
   - Excel raw row count
   - unique nickname count
   - Excel duplicate nicknames and conflicts
   - records to update
   - records to create
7. Write records.
   - Existing nickname: call `lark-cli base +record-upsert` with `--record-id`.
   - New nickname: prefer `lark-cli base +record-batch-create` for batches; use single-record upsert only for tiny or fallback cases.
   - Payload must contain only the four allowed fields, omitting empty optional values.
   - If writing JSON payloads via `--json @file`, put the temp payload in the current workspace and reference it as a relative path such as `@./xhs_create.json`; absolute paths under `/private/tmp` may not be accepted by `lark-cli`.
8. Verify.
   - Re-read the target records.
   - Confirm every expected nickname exists.
   - Confirm every non-empty Excel value for the four fields matches the Base value.
   - Report created, updated, skipped, missing, and mismatches.

## Preferred script

Use `scripts/lark_kol_update.py` for the repeatable path.

Example:

```bash
python3 ~/.codex/skills/xhs-upload-kol-to-lark/scripts/lark_kol_update.py \
  --excel artifacts/xhs-kol-info-10-1.xlsx \
  --excel artifacts/xhs-kol-info-page2-10.xlsx \
  --url 'https://my.feishu.cn/wiki/XpQDw2HVuiZvcxk08cZcLMzZn0b?table=tblD1BnWWO9pIxnX&view=vewfxCsqZ6' \
  --dry-run
```

After the user approves:

```bash
python3 ~/.codex/skills/xhs-upload-kol-to-lark/scripts/lark_kol_update.py \
  --excel artifacts/xhs-kol-info-10-1.xlsx \
  --excel artifacts/xhs-kol-info-page2-10.xlsx \
  --url 'https://my.feishu.cn/wiki/XpQDw2HVuiZvcxk08cZcLMzZn0b?table=tblD1BnWWO9pIxnX&view=vewfxCsqZ6' \
  --write
```

The script shells out to `lark-cli`, so keychain access may require rerunning with sandbox escalation.

## Auth and token notes

- If `lark-cli` reports missing config, keychain, DNS, or auth state, initialize/re-auth with `lark-cli config init --new`, complete browser authorization, then rerun the script.
- Wiki links have two tokens: the Wiki node token in the URL and the actual Base token returned by `wiki spaces get_node`. Always use the returned bitable `obj_token` for Base commands.
- For the recurring target table `tblD1BnWWO9pIxnX`, the table name has been `达人数据列表`; still verify with `+table-list` or field reads before writing because table names and schemas can drift.
- In the recurring table, `手机号` has appeared as a number field. Pure digit phone values should be written as JSON numbers; non-digit values must stop the run instead of being coerced.

## Safety rules

- Do not write before resolving the exact Base token and table ID.
- Do not write if Excel values conflict for the same nickname.
- Do not write if the Base already has duplicate `达人昵称`.
- Do not create or update fields; this skill only writes records.
- Do not write any Excel columns other than the four allowed fields.
- Treat `lark-cli` update notices as informational and mention them after completing the user task.

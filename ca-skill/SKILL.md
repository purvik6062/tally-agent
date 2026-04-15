---
emoji: 🧾
name: tally-prime-ca
version: 1.0.2
author: Maxxit
description: >-
  Full-service CA skill for TallyPrime running locally. Read accounting reports
  (day book, trial balance, P&L, balance sheet, outstandings, GST) and post or
  update vouchers (purchase/sales/payment/receipt/journal, credit note, debit
  note, contra) via TallyPrime XML-over-HTTP. Use when the user mentions Tally,
  accounting entries, invoices/bills, ledgers, outstanding, GST, returns, or
  financial statements.
disableModelInvocation: false
requires:
  env:
    - TALLY_URL
metadata:
  openclaw:
    requiredEnv:
      - TALLY_URL
    bins:
      - curl
    primaryCredential: TALLY_URL
---

# TallyPrime (CA) Skill

Connect to a **locally running** TallyPrime instance via its **XML-over-HTTP** interface. All requests are HTTP POST to `$TALLY_URL` (commonly `http://localhost:9000`) with an XML body.

- **No cloud API**: TallyPrime must be open/running on the user’s machine.
- **Multi-company**: Always use the correct `SVCURRENTCOMPANY` (exact spelling).

## Hero Use Case: WhatsApp invoice → Tally entry

Goal: zero manual entry for CAs handling many clients.

1. Read bill/invoice (PDF/image) and extract: company, party, GSTIN, date, invoice no, taxable, tax, total, ledger mapping.
2. Ensure masters exist: party ledger, purchase/sales ledger, GST ledger(s), bank/cash ledger (if needed).
3. Post voucher with a **unique GUID**.
4. Confirm a summary back to the user.

## When to use this skill

Use when the user asks to:

- Post entries: purchase, sales, receipt, payment, journal, contra, credit note, debit note
- Check reports: day book, trial balance, balance sheet, profit & loss, ledger statement, outstandings, GST
- Manage masters: create/alter ledgers, groups, stock items/UOM (inventory clients)
- Fix data: alter or cancel a voucher

## Critical rules (must follow)

1. **Never assume company**: if not explicit, ask which company to use before posting.
2. **Never guess ledgers**: verify ledgers exist before voucher import; create missing masters first.
3. **Dates are `YYYYMMDD`** (no separators).
4. **Idempotency**: always set a stable unique `GUID` per voucher to prevent duplicates on retries.
5. **Balance vouchers**: total debits must equal total credits (Tally error: “Voucher totals do not match!”).
6. **Escape XML**: narration/party names may contain `&` → use `&amp;` in XML.
7. **Posting is write operation**: confirm intent (and company) before any create/alter/cancel.
8. **Prefer bill-wise allocations** for party ledgers to keep outstandings correct (see `reference/vouchers.md`).
9. **Accounting-only vouchers (no inventory items)**: set `<ISINVOICE>No</ISINVOICE>` and place the **party ledger entry first** in the `ALLLEDGERENTRIES.LIST` sequence. This makes the Day Book "Particulars" column show the party name (not the expense/purchase ledger) and defaults the voucher to the clean "As Voucher" view. Only use `ISINVOICE=Yes` for item invoices that go through `reference/inventory.md`.
10. **Voucher imports must use `REPORTNAME=Vouchers`**. Do not use `All Masters` when creating vouchers. `All Masters` is only for master objects (ledger/group/stock item/etc).
11. **Normalize user dates before posting**: if user provides dates like `02-Feb-2026` / `02/02/2026`, convert to `20260202` in XML.

## Step 0: Check TallyPrime server

```bash
curl -s --max-time 5 "$TALLY_URL"
```

Expected (example):

```xml
<RESPONSE>TallyPrime Server is Running</RESPONSE>
```

If not running, stop and ask user to open TallyPrime and enable integrations for the port.

## Step 1: Company context

If the user did not specify company, ask. If they did, use **exact** name in `SVCURRENTCOMPANY`.

To list companies, use the template in `reference/reports.md` (“Company list”).

## Step 2: Verify/create required ledgers (masters)

Ledger existence checks and master creation templates are in `reference/masters.md` (includes ledgers, groups, and GST/address fields).

Quick group defaults (common CA mapping):

| Ledger type | Parent group |
|---|---|
| Customer | `Sundry Debtors` |
| Vendor | `Sundry Creditors` |
| Sales | `Sales Accounts` |
| Purchases/Expenses | `Purchase Accounts` / `Direct Expenses` / `Indirect Expenses` |
| Bank | `Bank Accounts` |
| Cash | `Cash-in-Hand` |
| GST | `Duties & Taxes` |

## Step 3: Post vouchers (core)

Use `REPORTNAME=Vouchers` and always include `GUID`, `DATE`, and `VOUCHERTYPENAME`. Full templates (including bill-wise allocations, returns, contra) are in `reference/vouchers.md`.

### If import returns `EXCEPTIONS=1` with no `LINEERROR`

Treat this as a schema/config mismatch and debug in this order:

1. Post a **minimal accounting voucher** (party + one counter ledger only) with:
   - `OBJVIEW="Accounting Voucher View"`
   - `ISINVOICE=No`
   - `REPORTNAME=Vouchers`
2. If minimal passes, add fields one-by-one:
   - GST lines
   - bill allocations
   - narration
   - optional round-off
3. If minimal fails:
   - Confirm exact `SVCURRENTCOMPANY` spelling
   - Confirm voucher type exists and allows accounting mode
   - Confirm date is within current FY and in `YYYYMMDD`
   - Export one manually entered voucher from Tally UI and replicate tags/signs exactly

Supported voucher types in this skill:

- Purchase, Sales, Payment, Receipt, Journal
- Credit Note, Debit Note
- Contra
- Voucher Alteration + Cancellation

## Read reports (core)

Use `TALLYREQUEST=Export` / `REPORTNAME=...` with `SVEXPORTFORMAT=$$SysName:XML`. Full templates are in `reference/reports.md`.

Common CA reports:

- Day Book (period)
- Trial Balance (period)
- Balance Sheet
- Profit and Loss
- Ledger Vouchers (ledger statement)
- Bills Receivable / Bills Payable (outstandings)
- Ledger Outstandings / Group Outstandings
- GST: GSTR-1 and related summaries (plus GSTR-3B where available)
- Stock Summary (inventory clients)

## Suggested GUID pattern

Use a deterministic pattern when invoice number exists:

```
{companyShort}-{voucherType}-{voucherNumber}-{date}
```

Examples:

- `abc-purchase-ril2026-00123-20260115`
- `abc-creditnote-cn09-20260302`

## Multi-company CA workflow (recommended)

1. Capture company name early (and confirm spelling).
2. Validate connectivity.
3. Fetch required ledgers/masters or create them.
4. Only then post the voucher.
5. Reply with: company, voucher type, voucher number, date, amount breakdown, and whether any masters were created.

## Advanced reference

- Reports and data export: `reference/reports.md`
- Voucher templates (including Debit/Credit Note, Contra, bill-wise allocations, alter/cancel): `reference/vouchers.md`
- Masters (ledgers/groups + GST/address, alteration): `reference/masters.md`
- Inventory (stock groups/items/UOM, item invoices): `reference/inventory.md`
- Error handling and troubleshooting: `reference/errors.md`

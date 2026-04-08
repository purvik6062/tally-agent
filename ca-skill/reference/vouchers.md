# Vouchers (Create / Alter / Cancel) — TallyPrime XML

This file contains **full voucher XML templates** for CA workflows, including returns (Credit/Debit Notes), Contra, bill-wise allocation, and safe update/cancel patterns.

## Conventions (must follow)

- Always set `SVCURRENTCOMPANY`.
- Always set `DATE` as `YYYYMMDD`.
- Always include a unique `GUID` for idempotency.
- For bills/outstanding tracking, include `BILLALLOCATIONS.LIST` on the **party ledger entry**.
- Ensure voucher totals match (sum of amounts = 0).
- Escape XML special characters (`&` → `&amp;`).

## Base template (Import Voucher)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="VOUCHER_TYPE" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <!-- voucher body -->
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Amount sign conventions (rule of thumb)

Tally’s sign conventions can vary by persisted view and voucher configuration. The most reliable method is: **create the voucher in Tally UI once, export to XML, and replicate the tags/signs**.

That said, many setups follow:

| Voucher | Party entry | Counter-ledger entry |
|---|---|---|
| Sales | Party debit (receivable) | Sales/GST credit |
| Purchase | Party credit (payable) | Purchase/GST debit |
| Receipt | Bank/Cash debit | Party credit |
| Payment | Party debit | Bank/Cash credit |

If Tally returns “Voucher totals do not match!”, adjust sign conventions to match the exported “known good” format.

## Bill-wise allocation snippet (attach to party ledger entry)

Use this on party ledger entries (customers/vendors) to keep outstandings accurate.

```xml
<BILLALLOCATIONS.LIST>
  <NAME>INVOICE_OR_REF</NAME>
  <BILLTYPE>New Ref</BILLTYPE>
  <AMOUNT>AMOUNT_SIGNED</AMOUNT>
</BILLALLOCATIONS.LIST>
```

Bill types: `New Ref`, `Agst Ref`, `Advance`, `On Account`.

## Sales (Invoice) — accounting-only

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
            <VOUCHERNUMBER>INVOICE_NO</VOUCHERNUMBER>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>Yes</ISINVOICE>
            <PARTYLEDGERNAME>CUSTOMER_LEDGER</PARTYLEDGERNAME>

            <!-- Party (customer) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CUSTOMER_LEDGER</LEDGERNAME>
              <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-TOTAL_AMOUNT</AMOUNT>
              <BILLALLOCATIONS.LIST>
                <NAME>INVOICE_NO</NAME>
                <BILLTYPE>New Ref</BILLTYPE>
                <AMOUNT>-TOTAL_AMOUNT</AMOUNT>
              </BILLALLOCATIONS.LIST>
            </ALLLEDGERENTRIES.LIST>

            <!-- Sales ledger -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>SALES_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- GST Output (optional) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST_OUTPUT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Purchase (Vendor bill) — accounting-only

For accounting-only purchases (no inventory items), set `ISINVOICE=No` and **emit the vendor/party ledger entry first**. This ensures:

- The Day Book "Particulars" column shows the **vendor name** instead of the purchase ledger.
- The voucher defaults to the plain "As Voucher" view, which is cleaner for non-item bills.

The same party-first ordering principle applies to any plain (non-item) voucher where you want the party name to appear in reports.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Purchase" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
            <VOUCHERNUMBER>BILL_NO</VOUCHERNUMBER>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>VENDOR_LEDGER</PARTYLEDGERNAME>

            <!-- Party (vendor) — FIRST so Particulars shows vendor name -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>VENDOR_LEDGER</LEDGERNAME>
              <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>TOTAL_AMOUNT</AMOUNT>
              <BILLALLOCATIONS.LIST>
                <NAME>BILL_NO</NAME>
                <BILLTYPE>New Ref</BILLTYPE>
                <AMOUNT>TOTAL_AMOUNT</AMOUNT>
              </BILLALLOCATIONS.LIST>
            </ALLLEDGERENTRIES.LIST>

            <!-- Purchase / expense -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>PURCHASE_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- GST Input (optional) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST_INPUT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Receipt (money received)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Receipt" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>CUSTOMER_LEDGER</PARTYLEDGERNAME>

            <!-- Bank/Cash (money in) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>BANK_OR_CASH_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Customer -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CUSTOMER_LEDGER</LEDGERNAME>
              <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Payment (money paid)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Payment" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>VENDOR_OR_EXPENSE_LEDGER</PARTYLEDGERNAME>

            <!-- Payee (vendor/expense) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>VENDOR_OR_EXPENSE_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Bank/Cash (money out) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>BANK_OR_CASH_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Journal (adjustments)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Journal" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>

            <!-- Debit -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>DEBIT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CREDIT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Credit Note (sales return)

Credit Note is commonly a separate voucher type configured in Tally. If your voucher type name differs, set `VCHTYPE` and `VOUCHERTYPENAME` accordingly.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Credit Note" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Credit Note</VOUCHERTYPENAME>
            <VOUCHERNUMBER>CN_NO</VOUCHERNUMBER>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>CUSTOMER_LEDGER</PARTYLEDGERNAME>

            <!-- Reduce sales / reverse tax as per configuration -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>SALES_RETURN_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST_OUTPUT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CUSTOMER_LEDGER</LEDGERNAME>
              <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>TOTAL_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Debit Note (purchase return)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Debit Note" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Debit Note</VOUCHERTYPENAME>
            <VOUCHERNUMBER>DN_NO</VOUCHERNUMBER>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>VENDOR_LEDGER</PARTYLEDGERNAME>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>PURCHASE_RETURN_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST_INPUT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>VENDOR_LEDGER</LEDGERNAME>
              <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-TOTAL_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Contra (bank transfers / cash deposit / withdrawal)

Contra vouchers are highly configuration-dependent. Use as a template and validate signs by exporting a known-good contra voucher from the client’s Tally.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Contra" ACTION="Create" OBJVIEW="Accounting Voucher View">
            <GUID>UNIQUE_GUID</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Contra</VOUCHERTYPENAME>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>

            <!-- From account -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>FROM_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- To account -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>TO_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Voucher alteration (edit existing)

Voucher identification typically requires a stable identifier (GUID or master ID). If you created the voucher via integration with a GUID, you can re-send with the same GUID and `ACTION="Alter"` (or use the documented alteration approach for your Tally setup).

Template (fill in the exact identifiers based on exported voucher XML):

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Sales" ACTION="Alter" OBJVIEW="Accounting Voucher View">
            <GUID>EXISTING_GUID</GUID>
            <!-- Include the full altered voucher content -->
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Voucher cancellation (void)

Cancellation is similar to alteration, but uses `ACTION="Cancel"` for the identified voucher.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Sales" ACTION="Cancel" OBJVIEW="Accounting Voucher View">
            <GUID>EXISTING_GUID</GUID>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Multi-line item invoices (inventory)

For itemized invoices using `ALLINVENTORYENTRIES.LIST` and `ACCOUNTINGALLOCATIONS.LIST`, see `reference/inventory.md`.


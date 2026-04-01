# Masters (Ledgers / Groups) — TallyPrime XML

This file contains templates to create and alter accounting masters that CAs routinely need: groups and ledgers (including address/GST fields where relevant).

## Conventions

- Master operations use `TALLYREQUEST=Import Data` and `REPORTNAME=All Masters`.
- Always include `SVCURRENTCOMPANY`.
- Create dependent masters first (e.g., group before ledger).

## Create Group

Example: create `North Zone Debtors` under `Sundry Debtors`.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <GROUP NAME="North Zone Debtors" ACTION="Create">
            <NAME>North Zone Debtors</NAME>
            <PARENT>Sundry Debtors</PARENT>
          </GROUP>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Create Ledger (minimal)

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <LEDGER NAME="LEDGER_NAME" ACTION="Create">
            <NAME>LEDGER_NAME</NAME>
            <PARENT>PARENT_GROUP</PARENT>
          </LEDGER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Create Ledger (with address / contact fields)

Field availability depends on enabled features. Safest workflow: create a sample ledger in UI and export it to XML, then copy required tags.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <LEDGER NAME="LEDGER_NAME" ACTION="Create">
            <NAME>LEDGER_NAME</NAME>
            <PARENT>PARENT_GROUP</PARENT>

            <MAILINGNAME.LIST TYPE="String">
              <MAILINGNAME>MAILING_NAME</MAILINGNAME>
            </MAILINGNAME.LIST>

            <ADDRESS.LIST TYPE="String">
              <ADDRESS>ADDRESS_LINE_1</ADDRESS>
              <ADDRESS>ADDRESS_LINE_2</ADDRESS>
              <ADDRESS>CITY</ADDRESS>
            </ADDRESS.LIST>

            <PINCODE>PIN</PINCODE>
            <COUNTRYNAME>India</COUNTRYNAME>
            <STATENAME>STATE_NAME</STATENAME>
            <EMAIL>EMAIL</EMAIL>
            <MOBILE>MOBILE</MOBILE>
            <LEDGERPHONE>PHONE</LEDGERPHONE>
          </LEDGER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Ledger alteration (update existing ledger)

Set `ACTION="Alter"` and send the desired fields.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <LEDGER NAME="LEDGER_NAME" ACTION="Alter">
            <NAME>LEDGER_NAME</NAME>
            <PARENT>NEW_PARENT_GROUP</PARENT>
          </LEDGER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>
```

## Ledger group reference (common CA mapping)

| Ledger Type | Parent Group |
|---|---|
| Customer (debtor) | `Sundry Debtors` |
| Vendor (creditor) | `Sundry Creditors` |
| Sales income | `Sales Accounts` |
| Purchases | `Purchase Accounts` |
| Direct costs | `Direct Expenses` |
| Indirect expenses | `Indirect Expenses` |
| Bank account | `Bank Accounts` |
| Cash | `Cash-in-Hand` |
| GST ledgers | `Duties & Taxes` |

## Check if a ledger exists (export list and search)

Use `List of Accounts` report to fetch masters in the company and confirm existence.

```xml
<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>
```

Then search the response for `<NAME>LEDGER_NAME</NAME>`.


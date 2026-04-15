import os
import re
import uuid
from datetime import datetime
from xml.sax.saxutils import escape

import requests
from dotenv import load_dotenv

load_dotenv()

TALLY_URL = os.getenv("TALLY_URL", "http://localhost:9000")
COMPANY = os.getenv("TALLY_COMPANY", "MyDemoCompany")


def _xml_escape(value: str) -> str:
    return escape(value or "", {'"': "&quot;", "'": "&apos;"})


def _normalize_date(date_value: str) -> str:
    raw = (date_value or "").strip()
    if not raw:
        raise ValueError("Date is required.")

    if re.fullmatch(r"\d{8}", raw):
        return raw

    # Accept common user-entered formats and normalize to YYYYMMDD.
    normalized = raw.replace("/", "-").replace(".", "-")
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = normalized.replace("–", "-")

    format_candidates = [
        "%d-%b-%Y",   # 02-Feb-2026
        "%d-%B-%Y",   # 02-February-2026
        "%d-%m-%Y",   # 02-02-2026
        "%Y-%m-%d",   # 2026-02-02
    ]
    for fmt in format_candidates:
        try:
            dt = datetime.strptime(normalized, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue

    raise ValueError(f"Unsupported date format: {date_value}. Use YYYYMMDD.")


def _summarize_import_response(response_text: str) -> str:
    tags = ["CREATED", "ALTERED", "DELETED", "ERRORS", "EXCEPTIONS", "LASTVCHID"]
    values = {}
    for tag in tags:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", response_text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            values[tag] = m.group(1).strip()

    line_errors = re.findall(r"<LINEERROR>(.*?)</LINEERROR>", response_text, flags=re.IGNORECASE | re.DOTALL)
    line_errors = [e.strip() for e in line_errors if e.strip()]

    if not values and not line_errors:
        return response_text

    summary_parts = []
    for key in ["CREATED", "ALTERED", "DELETED", "ERRORS", "EXCEPTIONS", "LASTVCHID"]:
        if key in values:
            summary_parts.append(f"{key}={values[key]}")
    summary = " | ".join(summary_parts)

    if line_errors:
        summary += "\nLINEERRORS:\n- " + "\n- ".join(line_errors)
    elif values.get("EXCEPTIONS") not in (None, "0") or values.get("ERRORS") not in (None, "0"):
        summary += "\nNo LINEERROR returned by Tally. Check company/voucher-type configuration and XML shape."

    return f"{summary}\n\nRAW_RESPONSE:\n{response_text}"

def send_to_tally(xml: str) -> str:
    try:
        response = requests.post(
            TALLY_URL,
            data=xml.encode("utf-8"),
            headers={"Content-Type": "application/xml"},
            timeout=10
        )
        return _summarize_import_response(response.text)
    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to TallyPrime. Is it open and running?"

def get_day_book(from_date: str, to_date: str) -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>Day Book</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
      <SVFROMDATE>{from_date}</SVFROMDATE>
      <SVTODATE>{to_date}</SVTODATE>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def get_trial_balance(from_date: str, to_date: str) -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>Trial Balance</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
      <SVFROMDATE>{from_date}</SVFROMDATE>
      <SVTODATE>{to_date}</SVTODATE>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def get_ledger_vouchers(ledger_name: str, from_date: str, to_date: str) -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>Ledger Vouchers</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
      <SVFROMDATE>{from_date}</SVFROMDATE>
      <SVTODATE>{to_date}</SVTODATE>
      <SVLEDGERNAME>{ledger_name}</SVLEDGERNAME>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def get_outstanding_receivables() -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>Bills Receivable</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def get_outstanding_payables() -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>Bills Payable</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def create_ledger(name: str, group: str) -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY><IMPORTDATA>
    <REQUESTDESC>
      <REPORTNAME>All Masters</REPORTNAME>
      <STATICVARIABLES><SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES>
    </REQUESTDESC>
    <REQUESTDATA>
      <TALLYMESSAGE xmlns:UDF="TallyUDF">
        <LEDGER NAME="{name}" ACTION="Create">
          <NAME>{name}</NAME>
          <PARENT>{group}</PARENT>
        </LEDGER>
      </TALLYMESSAGE>
    </REQUESTDATA>
  </IMPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def create_sales_invoice(
    party_name: str,
    sales_ledger: str,
    amount: float,
    date: str,
    voucher_number: str,
    narration: str = "",
    gst_ledger: str = None,
    gst_amount: float = 0
) -> str:
    guid = str(uuid.uuid4())
    date = _normalize_date(date)
    party_name = _xml_escape(party_name)
    sales_ledger = _xml_escape(sales_ledger)
    voucher_number = _xml_escape(voucher_number)
    narration = _xml_escape(narration)
    gst_ledger = _xml_escape(gst_ledger) if gst_ledger else None
    total = amount + gst_amount
    gst_entry = ""
    if gst_ledger and gst_amount > 0:
        gst_entry = f"""<ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>{gst_ledger}</LEDGERNAME>
      <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
      <AMOUNT>{gst_amount:.2f}</AMOUNT>
    </ALLLEDGERENTRIES.LIST>"""
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY><IMPORTDATA>
    <REQUESTDESC>
      <REPORTNAME>Vouchers</REPORTNAME>
      <STATICVARIABLES><SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES>
    </REQUESTDESC>
    <REQUESTDATA>
      <TALLYMESSAGE xmlns:UDF="TallyUDF">
        <VOUCHER VCHTYPE="Sales" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <GUID>{guid}</GUID>
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
          <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
          <NARRATION>{narration}</NARRATION>
          <ISINVOICE>No</ISINVOICE>
          <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_name}</LEDGERNAME>
            <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{total:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{sales_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          {gst_entry}
        </VOUCHER>
      </TALLYMESSAGE>
    </REQUESTDATA>
  </IMPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def create_purchase_bill(
    party_name: str,
    purchase_ledger: str,
    amount: float,
    date: str,
    voucher_number: str,
    narration: str = "",
    gst_ledger: str = None,
    gst_amount: float = 0
) -> str:
    guid = str(uuid.uuid4())
    date = _normalize_date(date)
    party_name = _xml_escape(party_name)
    purchase_ledger = _xml_escape(purchase_ledger)
    voucher_number = _xml_escape(voucher_number)
    narration = _xml_escape(narration)
    gst_ledger = _xml_escape(gst_ledger) if gst_ledger else None
    total = amount + gst_amount
    gst_entry = ""
    if gst_ledger and gst_amount > 0:
        gst_entry = f"""<ALLLEDGERENTRIES.LIST>
      <LEDGERNAME>{gst_ledger}</LEDGERNAME>
      <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
      <AMOUNT>-{gst_amount:.2f}</AMOUNT>
    </ALLLEDGERENTRIES.LIST>"""
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY><IMPORTDATA>
    <REQUESTDESC>
      <REPORTNAME>Vouchers</REPORTNAME>
      <STATICVARIABLES><SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES>
    </REQUESTDESC>
    <REQUESTDATA>
      <TALLYMESSAGE xmlns:UDF="TallyUDF">
        <VOUCHER VCHTYPE="Purchase" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <GUID>{guid}</GUID>
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
          <VOUCHERNUMBER>{voucher_number}</VOUCHERNUMBER>
          <NARRATION>{narration}</NARRATION>
          <ISINVOICE>No</ISINVOICE>
          <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_name}</LEDGERNAME>
            <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{total:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{purchase_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          {gst_entry}
        </VOUCHER>
      </TALLYMESSAGE>
    </REQUESTDATA>
  </IMPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def create_receipt(
    party_name: str,
    amount: float,
    bank_ledger: str,
    date: str,
    narration: str = ""
) -> str:
    guid = str(uuid.uuid4())
    date = _normalize_date(date)
    party_name = _xml_escape(party_name)
    bank_ledger = _xml_escape(bank_ledger)
    narration = _xml_escape(narration)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY><IMPORTDATA>
    <REQUESTDESC>
      <REPORTNAME>Vouchers</REPORTNAME>
      <STATICVARIABLES><SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES>
    </REQUESTDESC>
    <REQUESTDATA>
      <TALLYMESSAGE xmlns:UDF="TallyUDF">
        <VOUCHER VCHTYPE="Receipt" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <GUID>{guid}</GUID>
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ISINVOICE>No</ISINVOICE>
          <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{bank_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_name}</LEDGERNAME>
            <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
      </TALLYMESSAGE>
    </REQUESTDATA>
  </IMPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def create_payment(
    party_name: str,
    amount: float,
    bank_ledger: str,
    date: str,
    narration: str = ""
) -> str:
    guid = str(uuid.uuid4())
    date = _normalize_date(date)
    party_name = _xml_escape(party_name)
    bank_ledger = _xml_escape(bank_ledger)
    narration = _xml_escape(narration)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY><IMPORTDATA>
    <REQUESTDESC>
      <REPORTNAME>Vouchers</REPORTNAME>
      <STATICVARIABLES><SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY></STATICVARIABLES>
    </REQUESTDESC>
    <REQUESTDATA>
      <TALLYMESSAGE xmlns:UDF="TallyUDF">
        <VOUCHER VCHTYPE="Payment" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <GUID>{guid}</GUID>
          <DATE>{date}</DATE>
          <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
          <NARRATION>{narration}</NARRATION>
          <ISINVOICE>No</ISINVOICE>
          <PARTYLEDGERNAME>{party_name}</PARTYLEDGERNAME>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{bank_ledger}</LEDGERNAME>
            <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
            <AMOUNT>{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
            <LEDGERNAME>{party_name}</LEDGERNAME>
            <ISPARTYLEDGER>Yes</ISPARTYLEDGER>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
            <AMOUNT>-{amount:.2f}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
        </VOUCHER>
      </TALLYMESSAGE>
    </REQUESTDATA>
  </IMPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)

def get_gst_summary(from_date: str, to_date: str) -> str:
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY><EXPORTDATA><REQUESTDESC>
    <REPORTNAME>GSTR1</REPORTNAME>
    <STATICVARIABLES>
      <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
      <SVCURRENTCOMPANY>{COMPANY}</SVCURRENTCOMPANY>
      <SVFROMDATE>{from_date}</SVFROMDATE>
      <SVTODATE>{to_date}</SVTODATE>
    </STATICVARIABLES>
  </REQUESTDESC></EXPORTDATA></BODY>
</ENVELOPE>"""
    return send_to_tally(xml)
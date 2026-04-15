import os
from dotenv import load_dotenv
from tally_client import (
    get_day_book, get_trial_balance, get_ledger_vouchers,
    get_outstanding_receivables, get_outstanding_payables,
    create_ledger, create_sales_invoice, create_purchase_bill,
    create_receipt, create_payment, get_gst_summary
)

load_dotenv()

PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5")

# Load only the client we need
if PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print(f"✅ Using AI provider: {PROVIDER.upper()}")

# ─── Tools definition (shared by both providers) ───────────────────────
TOOLS = [
    {
        "name": "get_day_book",
        "description": "Get all transactions for a date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string", "description": "Start date YYYYMMDD"},
                "to_date":   {"type": "string", "description": "End date YYYYMMDD"}
            },
            "required": ["from_date", "to_date"]
        }
    },
    {
        "name": "get_trial_balance",
        "description": "Get all ledger balances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string"},
                "to_date":   {"type": "string"}
            },
            "required": ["from_date", "to_date"]
        }
    },
    {
        "name": "get_ledger_vouchers",
        "description": "Get all transactions for a specific ledger/party.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ledger_name": {"type": "string"},
                "from_date":   {"type": "string"},
                "to_date":     {"type": "string"}
            },
            "required": ["ledger_name", "from_date", "to_date"]
        }
    },
    {
        "name": "get_outstanding_receivables",
        "description": "Get unpaid customer invoices (money owed to us).",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_outstanding_payables",
        "description": "Get unpaid vendor bills (money we owe).",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "create_ledger",
        "description": "Create a new ledger (account) in Tally.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name":  {"type": "string"},
                "group": {"type": "string", "description": "e.g. Sundry Debtors, Sales Accounts"}
            },
            "required": ["name", "group"]
        }
    },
    {
        "name": "create_sales_invoice",
        "description": "Create a sales invoice in Tally.",
        "input_schema": {
            "type": "object",
            "properties": {
                "party_name":     {"type": "string"},
                "sales_ledger":   {"type": "string"},
                "amount":         {"type": "number"},
                "date":           {"type": "string"},
                "voucher_number": {"type": "string"},
                "narration":      {"type": "string"},
                "gst_ledger":     {"type": "string"},
                "gst_amount":     {"type": "number"}
            },
            "required": ["party_name", "sales_ledger", "amount", "date", "voucher_number"]
        }
    },
    {
        "name": "create_purchase_bill",
        "description": "Create a purchase bill in Tally.",
        "input_schema": {
            "type": "object",
            "properties": {
                "party_name":      {"type": "string"},
                "purchase_ledger": {"type": "string"},
                "amount":          {"type": "number"},
                "date":            {"type": "string"},
                "voucher_number":  {"type": "string"},
                "narration":       {"type": "string"},
                "gst_ledger":      {"type": "string"},
                "gst_amount":      {"type": "number"}
            },
            "required": ["party_name", "purchase_ledger", "amount", "date", "voucher_number"]
        }
    },
    {
        "name": "create_receipt",
        "description": "Record payment received from a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "party_name":  {"type": "string"},
                "amount":      {"type": "number"},
                "bank_ledger": {"type": "string"},
                "date":        {"type": "string"},
                "narration":   {"type": "string"}
            },
            "required": ["party_name", "amount", "bank_ledger", "date"]
        }
    },
    {
        "name": "create_payment",
        "description": "Record payment made to a vendor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "party_name":  {"type": "string"},
                "amount":      {"type": "number"},
                "bank_ledger": {"type": "string"},
                "date":        {"type": "string"},
                "narration":   {"type": "string"}
            },
            "required": ["party_name", "amount", "bank_ledger", "date"]
        }
    },
    {
        "name": "get_gst_summary",
        "description": "Get GST summary / GSTR-1 data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string"},
                "to_date":   {"type": "string"}
            },
            "required": ["from_date", "to_date"]
        }
    }
]

SYSTEM = """You are a helpful accounting assistant for an Indian business using TallyPrime.
Current financial year: 20250401 to 20260331. Use YYYYMMDD for all dates.
Always confirm before creating/writing data. Respond in the same language the user uses."""


# ─── Tool runner (same for both providers) ─────────────────────────────
def run_tool(name: str, inp: dict) -> str:
    try:
        if name == "get_day_book":               return get_day_book(inp["from_date"], inp["to_date"])
        if name == "get_trial_balance":          return get_trial_balance(inp["from_date"], inp["to_date"])
        if name == "get_ledger_vouchers":        return get_ledger_vouchers(inp["ledger_name"], inp["from_date"], inp["to_date"])
        if name == "get_outstanding_receivables":return get_outstanding_receivables()
        if name == "get_outstanding_payables":   return get_outstanding_payables()
        if name == "create_ledger":              return create_ledger(inp["name"], inp["group"])
        if name == "create_sales_invoice":       return create_sales_invoice(**inp)
        if name == "create_purchase_bill":       return create_purchase_bill(**inp)
        if name == "create_receipt":             return create_receipt(**inp)
        if name == "create_payment":             return create_payment(**inp)
        if name == "get_gst_summary":            return get_gst_summary(inp["from_date"], inp["to_date"])
        return "Tool not found."
    except Exception as exc:
        return f"ERROR while running {name}: {exc}"


# ─── OpenAI format converter ────────────────────────────────────────────
# OpenAI needs tools wrapped in {"type": "function", "function": {...}}
def to_openai_tools(tools):
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"]
            }
        }
        for t in tools
    ]


# ─── Main ask function ──────────────────────────────────────────────────
def ask(question: str) -> str:
    if PROVIDER == "openai":
        return ask_openai(question)
    else:
        return ask_anthropic(question)


# ─── OpenAI handler ─────────────────────────────────────────────────────
def ask_openai(question: str) -> str:
    import json
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": question}
    ]

    while True:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            tools=to_openai_tools(TOOLS),
            messages=messages
        )
        choice = response.choices[0]

        # Final answer — no tool call
        if choice.finish_reason == "stop":
            return choice.message.content

        # Tool call requested
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)  # add assistant message

            for tool_call in choice.message.tool_calls:
                name  = tool_call.function.name
                inp   = json.loads(tool_call.function.arguments)
                print(f"  🔧 {name}({inp})")
                result = run_tool(name, inp)

                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      result if isinstance(result, str) else json.dumps(result)
                })


# ─── Anthropic handler ──────────────────────────────────────────────────
def ask_anthropic(question: str) -> str:
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return next((b.text for b in response.content if hasattr(b, "text")), "Done.")

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 {block.name}({block.input})")
                    results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     run_tool(block.name, block.input)
                    })
            messages.append({"role": "user", "content": results})
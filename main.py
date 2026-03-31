from ai_agent import ask

print("🤖 TallyPrime AI Assistant")
print("Type your question. Type 'exit' to quit.\n")

while True:
    q = input("You: ").strip()
    if q.lower() in ("exit", "quit"): break
    if not q: continue
    print("  ⏳ Thinking...")
    print(f"\n🤖 {ask(q)}\n")
    print("-" * 60)
"""
seed_data.py
Populates the OhmBot-Support Opik project with 30 days of synthetic
production traces. Skips automatically if data already exists.
"""
import os
import sys
import opik
import random
import uuid
from datetime import datetime, timedelta, timezone

# ── tqdm is already available in Colab; fall back gracefully if not ────────────
try:
    from tqdm.auto import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        print(kwargs.get("desc", ""), "...")
        return iterable

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_NAME = os.environ.get("OPIK_PROJECT_NAME", "OhmSweetOhm-Support-Chatbot-Opik-Workshop")
NUM_THREADS  = 75    # ~150-200 traces total, runs in ~25 seconds
DAYS_BACK    = 30
MODEL        = "gpt-5"

# ──────────────────────────────────────────────────────────────────────────────
# SKIP GUARD — don't re-seed if the project already has traces
# ──────────────────────────────────────────────────────────────────────────────
opik.configure(use_local=False)
client = opik.Opik(project_name=PROJECT_NAME)

try:
    existing = client.search_traces(project_name=PROJECT_NAME, max_results=1)
    if existing:
        print("✅ Demo data already exists — skipping seed.")
        sys.exit(0)
except Exception:
    pass  # Project doesn't exist yet, continue with seeding

# ──────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA  (matched to ohm_sweet_ohm.db schema)
# ──────────────────────────────────────────────────────────────────────────────
DATABASE_QUESTIONS = [
    "How many AirStream Wireless Earbuds do you have in stock?",
    "Is the NexGen Pro Gaming Console available?",
    "Do you have the CrystalView 4K Smart TV in 65 inch?",
    "What's the stock level for the PlayStation 5?",
    "Are there any PulseSync Fitness Trackers left?",
    "How much does the NexusWave Pro Headphones cost?",
    "What is the price of the BudgetSmart LED TV 55 inch?",
    "How much is the ProGamer Controller?",
    "Where is my order? My order ID is ORD-10482.",
    "Can you check the status of order ORD-77210?",
    "Has my order ORD-33891 shipped yet?",
    "What's the current location of order ORD-55124?",
    "Are there any deals on gaming products right now?",
    "Is the SonicBlast Studio Headphones on sale?",
    "What promotions are running on TVs?",
    "Which stores carry the Racing Wheel Pro?",
    "What audio products are currently discounted?",
]
DATABASE_ANSWERS = [
    "The AirStream Wireless Earbuds (AUDIO-103) currently have 47 units in stock.",
    "Yes, the NexGen Pro Gaming Console (GAME-1101) is available with 12 units remaining.",
    "The CrystalView 4K Smart TV 65\" (TV-1301-65) has 8 units in stock.",
    "The PlayStation 5 (GAME-1102) is currently out of stock. We expect restocking next week.",
    "Yes, the PulseSync Fitness Tracker (WEAR-201) has 31 units available.",
    "The NexusWave Pro Headphones (AUDIO-101) are priced at $349.99.",
    "The BudgetSmart LED TV 55\" (TV-1303-55) is priced at $399.99.",
    "The ProGamer Controller (GAME-1201) is priced at $69.99.",
    "Order ORD-10482 is currently in transit and estimated to arrive within 2 business days.",
    "Order ORD-77210 shipped yesterday via FedEx. Tracking number: FX-9921047.",
    "Order ORD-33891 has shipped and is currently out for delivery.",
    "Order ORD-55124 is currently at the regional sorting facility in Dallas, TX.",
    "Yes! There's currently a 20% discount on all GAME category products through end of month.",
    "The SonicBlast Studio Headphones (AUDIO-102) have a $40 discount applied right now.",
    "The BudgetSmart LED TV range has a 15% promotional discount running this week.",
    "The Racing Wheel Pro is stocked at 6 store locations. The nearest to you is Store S-04.",
    "The NexusWave Pro Headphones and AirStream Earbuds both have active promotions.",
]
DATABASE_SQLS = [
    "SELECT stock_level FROM store_inventory si JOIN products p ON si.product_id = p.product_id WHERE p.name LIKE '%AirStream Wireless Earbuds%'",
    "SELECT in_stock, name FROM products WHERE product_id = 'GAME-1101'",
    "SELECT in_stock FROM products WHERE product_id = 'TV-1301-65'",
    "SELECT in_stock FROM products WHERE product_id = 'GAME-1102'",
    "SELECT in_stock FROM products WHERE product_id = 'WEAR-201'",
    "SELECT price FROM products WHERE product_id = 'AUDIO-101'",
    "SELECT price FROM products WHERE product_id = 'TV-1303-55'",
    "SELECT price FROM products WHERE product_id = 'GAME-1201'",
    "SELECT status, current_location, days_since_order FROM orders WHERE order_id = 'ORD-10482'",
    "SELECT status, current_location FROM orders WHERE order_id = 'ORD-77210'",
    "SELECT status, current_location FROM orders WHERE order_id = 'ORD-33891'",
    "SELECT current_location, status FROM orders WHERE order_id = 'ORD-55124'",
    "SELECT p.name, pr.discount_percent FROM promotions pr JOIN products p ON pr.product_ids LIKE '%' || p.product_id || '%' WHERE p.category = 'GAME'",
    "SELECT p.name, pr.discount_amount FROM promotions pr JOIN products p ON pr.product_ids LIKE '%AUDIO-102%'",
    "SELECT p.name, pr.discount_percent FROM promotions pr JOIN products p ON p.category = 'TV' AND pr.product_ids LIKE '%' || p.product_id || '%'",
    "SELECT s.store_id, si.stock_level FROM store_inventory si JOIN stores s ON si.store_id = s.store_id JOIN products p ON si.product_id = p.product_id WHERE p.product_id = 'GAME-1202'",
    "SELECT p.name, pr.discount_amount FROM promotions pr JOIN products p ON pr.product_ids LIKE '%' || p.product_id || '%' WHERE p.category = 'AUDIO'",
]

POLICY_QUESTIONS = [
    "What is your return policy?",
    "How long does standard shipping take?",
    "Do you offer a warranty on electronics?",
    "Can I return a TV after 30 days if it's unopened?",
    "What happens if my item arrives damaged?",
    "Do you ship internationally?",
    "Is there a restocking fee for returned gaming consoles?",
    "What does the warranty cover on headphones?",
    "How do I initiate a return for my order?",
    "Does the warranty cover the NexGen Pro Gaming Console?",
]
POLICY_ANSWERS = [
    "We accept returns within 30 days of purchase with proof of receipt for all items in original condition.",
    "Standard shipping takes 5–7 business days. Express shipping (2-day) is available at checkout.",
    "All electronics carry a 1-year limited manufacturer warranty covering defects in materials and workmanship.",
    "Unopened TVs may be returned within 30 days. Large-screen TVs (65\"+) require a scheduled pickup.",
    "If your item arrives damaged, contact us within 48 hours with a photo and we'll send a replacement or issue a full refund.",
    "We ship to over 40 countries. International delivery takes 10–14 business days and customs fees may apply.",
    "Gaming consoles are subject to a 15% restocking fee if opened. Unopened units carry no restocking fee.",
    "Headphone warranties cover manufacturing defects and driver failures but not physical damage or water damage.",
    "To initiate a return, visit your order history, select the item, and click 'Request Return'. You'll receive a prepaid label within 24 hours.",
    "Yes, the NexGen Pro Gaming Console is covered by a 1-year manufacturer warranty from the purchase date.",
]
POLICY_CONTEXTS = [
    "Return Policy: All items eligible for return within 30 days in original condition with receipt...",
    "Shipping Policy: Standard 5-7 business days. Express 2-day available. Free standard shipping on orders over $50...",
    "Warranty Policy: 1-year limited warranty on all electronics covering defects in materials and workmanship...",
    "Extended Returns: Large TVs require scheduled pickup for returns. Unopened items accepted up to 30 days...",
    "Damaged Items: Customer must report within 48 hours with photographic evidence. Replacement or full refund issued...",
    "International Shipping: Available to 40+ countries. 10-14 business day delivery. Customs fees are customer responsibility...",
    "Restocking Fees: 15% restocking fee applies to opened gaming hardware. No fee for unopened items...",
    "Headphone Warranty: Covers driver failure and manufacturing defects. Excludes physical damage, water damage, and wear...",
    "Returns Process: Initiate via order history portal. Prepaid return label emailed within 24 hours of request...",
    "Product Warranty: NexGen Pro Gaming Console covered under standard 1-year limited warranty from purchase date...",
]

CHAT_QUESTIONS = [
    "Hi, can you help me?",
    "Thanks, that answered my question!",
    "Okay got it, appreciate the help.",
    "You're really helpful, thank you!",
    "No that's all I needed, thanks.",
    "Hello!",
    "Great, I'll go ahead and place the order.",
    "Perfect, that's exactly what I was looking for.",
    "Sounds good, talk later!",
    "Thanks for looking that up!",
]
CHAT_ANSWERS = [
    "Of course! What can I help you with today?",
    "Happy to help! Let me know if anything else comes up.",
    "Anytime! Don't hesitate to reach out.",
    "Glad I could assist! Is there anything else you need?",
    "Great! Come back if you have any other questions.",
    "Hi there! How can I assist you today?",
    "Sounds great! Feel free to reach out if you need anything after your order arrives.",
    "Wonderful! Let me know if you need help with anything else.",
    "Take care! We're here if you need us.",
    "My pleasure! Let me know if there's anything else I can help with.",
]

ROUTE_WEIGHTS = [0.50, 0.35, 0.15]  # DATABASE, POLICY, CHAT

MERMAID_GRAPH = """graph TD;
Start(User Input)-->Router{Router};
Router-->|DATABASE| SQL[SQL Workflow];
Router-->|POLICY| RAG[Policy Workflow];
Router-->|CHAT| Chat[General Chat];
SQL-->SQLTool[DB Query];
RAG-->RAGTool[Vector Search];
Chat-->End(Response);"""

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def make_usage(in_lo, in_hi, out_lo, out_hi):
    p = random.randint(in_lo, in_hi)
    c = random.randint(out_lo, out_hi)
    return {"prompt_tokens": p, "completion_tokens": c, "total_tokens": p + c}

def helpfulness_score():
    return random.choices([1.0, 0.75, 0.5, 0.25, 0.0], weights=[45, 30, 15, 7, 3])[0]

def classification_score():
    return 1.0 if random.random() < 0.88 else 0.0

def frustration_score(turn_scores):
    base = random.choices([0.0, 0.1, 0.3, 0.6, 0.9, 1.0], weights=[35, 25, 20, 10, 7, 3])[0]
    # Nudge frustration up if helpfulness was consistently low
    avg_helpfulness = sum(turn_scores) / len(turn_scores) if turn_scores else 1.0
    if avg_helpfulness < 0.4:
        base = min(1.0, base + 0.3)
    return round(base, 2)

# ──────────────────────────────────────────────────────────────────────────────
# TRACE BUILDER — mirrors the real OhmBot span hierarchy exactly
# Returns only the final answer so it can be appended to chat_history
# ──────────────────────────────────────────────────────────────────────────────
def log_trace(thread_id, turn_index, question, chat_history, trace_start):
    route     = random.choices(["DATABASE", "POLICY", "CHAT"], weights=ROUTE_WEIGHTS)[0]
    total_dur = random.uniform(1.2, 9.0)
    t         = trace_start

    # ── Root trace ─────────────────────────────────────────────────────────
    trace = client.trace(
        name         = "OhmBot_Support",
        project_name = PROJECT_NAME,
        input        = {"user_question": question, "chat_history": chat_history},
        output       = None,
        tags         = ["production", route.lower()],
        metadata     = {
            "environment": "production",
            "session_id" : thread_id,
            "turn_index" : turn_index,
            "_opik_graph_definition": {"format": "mermaid", "data": MERMAID_GRAPH},
        },
        thread_id    = thread_id,
        start_time   = t,
    )

    # ── Router span ────────────────────────────────────────────────────────
    router_dur  = random.uniform(0.3, 0.9)
    router_span = trace.span(
        name       = "route_user_request",
        type       = "llm",
        model      = MODEL,
        provider   = "openai",
        input      = {"messages": [{"role": "user", "content": f"Classify: {question}"}]},
        output     = {"choices": [{"message": {"content": route}}]},
        usage      = make_usage(30, 120, 1, 5),
        start_time = t,
        end_time   = t + timedelta(seconds=router_dur),
        metadata   = {"temperature": 0},
    )
    router_span.log_feedback_score(
        name   = "classification_correctness",
        value  = classification_score(),
        reason = f"Routed to {route}",
    )
    router_span.end()
    t += timedelta(seconds=router_dur)

    # ── Workflow branches ──────────────────────────────────────────────────
    final_answer = ""

    if route == "DATABASE":
        idx          = random.randrange(len(DATABASE_QUESTIONS))
        sql          = DATABASE_SQLS[idx]
        final_answer = DATABASE_ANSWERS[idx]

        sql_gen_dur = random.uniform(0.8, 2.5)
        sql_gen = trace.span(
            name       = "SQL_Generation_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"tool_call": {"name": "run_sql_query", "arguments": {"query": sql}}},
            usage      = make_usage(150, 400, 20, 60),
            start_time = t,
            end_time   = t + timedelta(seconds=sql_gen_dur),
        )
        sql_gen.end()
        t += timedelta(seconds=sql_gen_dur)

        tool_dur  = random.uniform(0.05, 0.3)
        tool_span = trace.span(
            name       = "run_sql_query",
            type       = "tool",
            input      = {"query": sql},
            output     = {"result": "| col1 | col2 |\n|------|------|\n| val1 | val2 |"},
            start_time = t,
            end_time   = t + timedelta(seconds=tool_dur),
            metadata   = {"database": "ohm_sweet_ohm.db"},
        )
        tool_span.end()
        t += timedelta(seconds=tool_dur)

        final_dur  = random.uniform(0.5, 1.5)
        final_span = trace.span(
            name       = "SQL_Final_Answer_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"choices": [{"message": {"content": final_answer}}]},
            usage      = make_usage(200, 500, 40, 150),
            start_time = t,
            end_time   = t + timedelta(seconds=final_dur),
        )
        final_span.end()

    elif route == "POLICY":
        idx          = random.randrange(len(POLICY_QUESTIONS))
        context      = POLICY_CONTEXTS[idx]
        final_answer = POLICY_ANSWERS[idx]

        rag_gen_dur = random.uniform(0.6, 1.8)
        rag_gen = trace.span(
            name       = "RAG_Query_Generation",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"tool_call": {"name": "look_up_policy", "arguments": {"query": question}}},
            usage      = make_usage(100, 300, 10, 40),
            start_time = t,
            end_time   = t + timedelta(seconds=rag_gen_dur),
        )
        rag_gen.end()
        t += timedelta(seconds=rag_gen_dur)

        retrieval_dur  = random.uniform(0.1, 0.5)
        retrieval_span = trace.span(
            name       = "look_up_policy",
            type       = "tool",
            input      = {"query": question},
            output     = {"chunks": [context], "n_results": random.randint(1, 3)},
            start_time = t,
            end_time   = t + timedelta(seconds=retrieval_dur),
            metadata   = {"index": "faq.txt"},
        )
        retrieval_span.end()
        t += timedelta(seconds=retrieval_dur)

        final_dur  = random.uniform(0.6, 2.0)
        final_span = trace.span(
            name       = "RAG_Final_Answer_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [
                {"role": "system", "content": "You are a policy assistant. Use the handbook."},
                {"role": "tool",   "content": context},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": final_answer}}]},
            usage      = make_usage(250, 600, 50, 200),
            start_time = t,
            end_time   = t + timedelta(seconds=final_dur),
        )
        final_span.end()

    else:  # CHAT
        idx          = random.randrange(len(CHAT_QUESTIONS))
        final_answer = CHAT_ANSWERS[idx]
        chat_dur     = random.uniform(0.4, 1.2)
        chat_span    = trace.span(
            name       = "run_chat_workflow",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": final_answer}}]},
            usage      = make_usage(50, 150, 20, 80),
            start_time = t,
            end_time   = t + timedelta(seconds=chat_dur),
        )
        chat_span.end()

    # ── Close root trace ───────────────────────────────────────────────────
    trace.end(
        end_time = trace_start + timedelta(seconds=total_dur),
        output   = {"response": final_answer},
    )
    trace.log_feedback_score(
        name   = "answer_helpfulness",
        value  = helpfulness_score(),
        reason = "Synthetic user rating",
    )

    # Return only the answer — used to build chat_history for the next turn
    return final_answer


# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────────
now          = datetime.now(timezone.utc)
total_traces = 0

for _ in tqdm(range(NUM_THREADS), desc="Seeding OhmBot traces", unit="thread"):
    thread_id    = f"session-{uuid.uuid4().hex[:12]}"
    num_turns    = random.choices([1, 2, 3, 4, 5], weights=[40, 25, 18, 10, 7])[0]
    days_ago     = random.betavariate(2, 5) * DAYS_BACK
    thread_start = now - timedelta(days=days_ago, minutes=random.randint(0, 120))

    chat_history = []
    turn_scores  = []

    for turn in range(num_turns):
        turn_start = thread_start + timedelta(minutes=turn * random.uniform(1, 8))
        route_hint = random.choices(["DATABASE", "POLICY", "CHAT"], weights=ROUTE_WEIGHTS)[0]

        if route_hint == "DATABASE":
            question = random.choice(DATABASE_QUESTIONS)
        elif route_hint == "POLICY":
            question = random.choice(POLICY_QUESTIONS)
        else:
            question = random.choice(CHAT_QUESTIONS)

        answer = log_trace(
            thread_id    = thread_id,
            turn_index   = turn,
            question     = question,
            chat_history = chat_history,
            trace_start  = turn_start,
        )

        # Track helpfulness for frustration calculation at thread close
        turn_scores.append(helpfulness_score())

        # Build conversation history for the next turn
        chat_history.append({"role": "user",      "content": question})
        chat_history.append({"role": "assistant",  "content": answer})
        total_traces += 1

    # ── Close the thread and log frustration score directly against it ─────
    client.traces.close_trace_thread(thread_id=thread_id)
    client.log_threads_feedback_scores(
        scores=[{
            "id"    : thread_id,
            "name"  : "user_frustration",
            "value" : frustration_score(turn_scores),
            "reason": f"{num_turns} turn(s), avg helpfulness {sum(turn_scores)/len(turn_scores):.2f}",
        }]
    )

client.flush()
print(f"✅ Seeded {total_traces} traces across {NUM_THREADS} threads into '{PROJECT_NAME}'.")

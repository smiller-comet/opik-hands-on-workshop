"""
seed_data.py
Populates the OhmSweetOhm-Support-Chatbot-Opik-Workshop Opik project with 30 days
of synthetic production traces. Skips automatically if data already exists.

Note on Historical Timestamps:
Traces are created with historical start_time and end_time values to simulate
production data from the past 30 days. To ensure traces appear in dashboards
under their historical dates (not ingestion date), trace and span IDs are generated
using id_helpers.generate_id() with the historical timestamp. This is critical
for proper date grouping in Opik dashboards.
"""

import os
import sys
import opik
from opik import id_helpers
import random
import uuid
import time
import signal
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
# NUM_THREADS: Set to generate ~500 traces
# Expected traces per thread = 2.05 (weighted avg of 1-4 turns: 35%, 35%, 20%, 10%)
# 250 threads * 2.05 ≈ 512 traces
NUM_THREADS  = 250
DAYS_BACK    = 30
MODEL        = "gpt-5"
# Performance optimization: Opik queues traces internally, so we don't need to flush during the loop
# This avoids blocking on rate limits and makes trace creation much faster
# We'll only flush at the end to ensure all data is sent
FLUSH_INTERVAL = None  # Disable periodic flushing - flush only at end

# ──────────────────────────────────────────────────────────────────────────────
# SKIP GUARD
# ──────────────────────────────────────────────────────────────────────────────
opik.configure(use_local=False)
client = opik.Opik(project_name=PROJECT_NAME)

try:
    existing = client.search_traces(project_name=PROJECT_NAME, max_results=1)
    if existing:
        print("✅ Demo data already exists — skipping seed.")
        sys.exit(0)
except Exception:
    pass

# ──────────────────────────────────────────────────────────────────────────────
# CONVERSATION DATA
# Each entry is a tuple of (question, answer, sql) so they always stay matched.
# follow_ups are realistic second/third turn messages that continue the thread.
# ──────────────────────────────────────────────────────────────────────────────
DATABASE_TURNS = [
    {
        "question": "How many AirStream Wireless Earbuds do you have in stock?",
        "answer":   "The AirStream Wireless Earbuds (AUDIO-103) currently have 47 units in stock.",
        "sql":      "SELECT stock_level FROM store_inventory si JOIN products p ON si.product_id = p.product_id WHERE p.name LIKE '%AirStream Wireless Earbuds%'",
        "follow_ups": [
            ("Are they available in white?",           "Yes, the AirStream Wireless Earbuds are available in white, black, and navy blue."),
            ("Great, what's the price?",               "The AirStream Wireless Earbuds are priced at $79.99."),
            ("Do they come with a warranty?",          "Yes, all Ohm audio products include a 1-year limited warranty."),
        ]
    },
    {
        "question": "Is the NexGen Pro Gaming Console available?",
        "answer":   "Yes, the NexGen Pro Gaming Console (GAME-1101) is available with 12 units remaining.",
        "sql":      "SELECT in_stock, name FROM products WHERE product_id = 'GAME-1101'",
        "follow_ups": [
            ("How much does it cost?",                 "The NexGen Pro Gaming Console is priced at $499.99."),
            ("Does it come with any games?",           "The NexGen Pro Gaming Console comes bundled with one controller and a 1-month game pass."),
            ("Can I pick it up in store?",             "Yes, you can reserve it for in-store pickup. Which city are you located in?"),
        ]
    },
    {
        "question": "Do you have the CrystalView 4K Smart TV in 65 inch?",
        "answer":   "The CrystalView 4K Smart TV 65\" (TV-1301-65) has 8 units in stock.",
        "sql":      "SELECT in_stock FROM products WHERE product_id = 'TV-1301-65'",
        "follow_ups": [
            ("What's the price on that?",              "The CrystalView 4K Smart TV 65\" is priced at $1,199.99."),
            ("Is there a wall mount included?",        "The TV does not include a wall mount, but we carry compatible mounts starting at $39.99."),
            ("What's the return policy on TVs?",       "TVs can be returned within 30 days. Units 65\" and larger require a scheduled pickup."),
        ]
    },
    {
        "question": "What's the stock level for the PlayStation 5?",
        "answer":   "The PlayStation 5 (GAME-1102) is currently out of stock. We expect restocking next week.",
        "sql":      "SELECT in_stock FROM products WHERE product_id = 'GAME-1102'",
        "follow_ups": [
            ("Can I be notified when it's back?",      "Yes! You can sign up for a restock alert on the product page and we'll email you immediately."),
            ("Do you have any PS5 bundles?",           "We currently have a PS5 + extra controller bundle reserved for the restock. Would you like to be added to the waitlist?"),
            ("What about the NexGen Pro instead?",     "The NexGen Pro Gaming Console (GAME-1101) is available now with 12 units in stock at $499.99."),
        ]
    },
    {
        "question": "How much does the NexusWave Pro Headphones cost?",
        "answer":   "The NexusWave Pro Headphones (AUDIO-101) are priced at $349.99.",
        "sql":      "SELECT price FROM products WHERE product_id = 'AUDIO-101'",
        "follow_ups": [
            ("Is there any discount available?",       "There is currently a $30 promotional discount on the NexusWave Pro, bringing it to $319.99."),
            ("How do they compare to the SonicBlast?", "The NexusWave Pro offers active noise cancellation and 30-hour battery life. The SonicBlast is studio-focused with a flatter sound profile."),
            ("What's the return policy if I don't like them?", "Headphones can be returned within 30 days in original condition with receipt."),
        ]
    },
    {
        "question": "Where is my order? My order ID is ORD-10482.",
        "answer":   "Order ORD-10482 is currently in transit and estimated to arrive within 2 business days.",
        "sql":      "SELECT status, current_location, days_since_order FROM orders WHERE order_id = 'ORD-10482'",
        "follow_ups": [
            ("Which carrier is handling it?",          "Order ORD-10482 is being shipped via UPS. Your tracking number is 1Z999AA10123456784."),
            ("Can I change the delivery address?",     "Address changes are possible if the order hasn't reached the final sorting facility. I'll flag this for our shipping team."),
            ("What if it doesn't arrive on time?",     "If your order is delayed past the estimated delivery date, contact us and we'll initiate an investigation with the carrier."),
        ]
    },
    {
        "question": "Can you check the status of order ORD-77210?",
        "answer":   "Order ORD-77210 shipped yesterday via FedEx. Tracking number: FX-9921047.",
        "sql":      "SELECT status, current_location FROM orders WHERE order_id = 'ORD-77210'",
        "follow_ups": [
            ("When is the expected delivery?",         "Based on the FedEx tracking, ORD-77210 is expected to arrive this Thursday."),
            ("Can I see what's in that order?",        "Order ORD-77210 contains: 1x NexusWave Pro Headphones and 1x MultiCharge Cable Set."),
            ("Thanks, that's all I needed.",           "Great! Don't hesitate to reach out if anything else comes up."),
        ]
    },
    {
        "question": "Are there any deals on gaming products right now?",
        "answer":   "Yes! There's currently a 20% discount on all GAME category products through end of month.",
        "sql":      "SELECT p.name, pr.discount_percent FROM promotions pr JOIN products p ON pr.product_ids LIKE '%' || p.product_id || '%' WHERE p.category = 'GAME'",
        "follow_ups": [
            ("Does that include the NexGen Pro Console?", "Yes, the NexGen Pro Gaming Console is included in the promotion — 20% off brings it to $399.99."),
            ("What about the ProGamer Controller?",    "Yes, the ProGamer Controller is also 20% off, down to $55.99 from $69.99."),
            ("How long is the sale running?",          "The gaming promotion runs through the end of this month."),
        ]
    },
    {
        "question": "What is the price of the BudgetSmart LED TV 55 inch?",
        "answer":   "The BudgetSmart LED TV 55\" (TV-1303-55) is priced at $399.99.",
        "sql":      "SELECT price FROM products WHERE product_id = 'TV-1303-55'",
        "follow_ups": [
            ("Is there a 65 inch version?",            "Yes, the BudgetSmart LED TV 65\" (TV-1303-65) is available at $549.99."),
            ("Does it support 4K?",                    "The BudgetSmart LED TV supports 4K resolution with HDR and built-in smart TV features."),
            ("Any promotions on it right now?",        "The BudgetSmart LED TV range has a 15% promotional discount running this week."),
        ]
    },
]

POLICY_TURNS = [
    {
        "question": "What is your return policy?",
        "answer":   "We accept returns within 30 days of purchase with proof of receipt for all items in original condition.",
        "context":  "Return Policy: All items eligible for return within 30 days in original condition with receipt...",
        "follow_ups": [
            ("What if I lost my receipt?",             "Without a receipt, we can look up your purchase using the order ID or the email address used at checkout."),
            ("Can I return an opened item?",           "Opened items are returnable within 30 days. Some categories like gaming hardware have a 15% restocking fee if opened."),
            ("How long does the refund take?",         "Refunds are processed within 3-5 business days after we receive the item."),
        ]
    },
    {
        "question": "How long does standard shipping take?",
        "answer":   "Standard shipping takes 5–7 business days. Express shipping (2-day) is available at checkout.",
        "context":  "Shipping Policy: Standard 5-7 business days. Express 2-day available...",
        "follow_ups": [
            ("Is there free shipping?",                "Yes, standard shipping is free on all orders over $50."),
            ("Can I upgrade to express after ordering?", "Shipping upgrades are possible if the order hasn't been picked up by the carrier yet. Contact us immediately after placing your order."),
            ("Do you ship on weekends?",               "Orders placed Friday after 3pm through Sunday will begin processing on Monday."),
        ]
    },
    {
        "question": "Do you offer a warranty on electronics?",
        "answer":   "All electronics carry a 1-year limited manufacturer warranty covering defects in materials and workmanship.",
        "context":  "Warranty Policy: 1-year limited warranty on all electronics...",
        "follow_ups": [
            ("Does it cover accidental damage?",       "The standard warranty does not cover accidental damage. We do offer an extended protection plan that covers accidental damage for an additional fee."),
            ("How do I make a warranty claim?",        "To make a warranty claim, contact our support team with your order ID and a description of the issue. We'll guide you through the process."),
            ("Can I extend the warranty?",             "Yes, we offer 2-year and 3-year extended protection plans available for purchase within 30 days of your order."),
        ]
    },
    {
        "question": "What happens if my item arrives damaged?",
        "answer":   "If your item arrives damaged, contact us within 48 hours with a photo and we'll send a replacement or issue a full refund.",
        "context":  "Damaged Items: Customer must report within 48 hours with photographic evidence...",
        "follow_ups": [
            ("Do I need to return the damaged item?",  "For most damaged items, we don't require a return — we'll send a replacement immediately after verifying the damage photo."),
            ("What if it's been more than 48 hours?",  "We recommend contacting us as soon as possible. While the 48-hour window is our standard policy, we review late reports on a case-by-case basis."),
            ("How quickly will the replacement arrive?", "Replacement orders are prioritized and typically shipped within 24 hours via express delivery."),
        ]
    },
    {
        "question": "Do you ship internationally?",
        "answer":   "We ship to over 40 countries. International delivery takes 10–14 business days and customs fees may apply.",
        "context":  "International Shipping: Available to 40+ countries. 10-14 business day delivery...",
        "follow_ups": [
            ("Which countries do you ship to?",        "We ship to most countries in Europe, Asia-Pacific, and North America. You can see the full list at checkout when entering your address."),
            ("Who pays the customs fees?",             "Customs and import duties are the responsibility of the recipient and vary by country."),
            ("Is express international shipping available?", "We offer international express shipping (5-7 days) to select countries for an additional fee."),
        ]
    },
    {
        "question": "Is there a restocking fee for returned gaming consoles?",
        "answer":   "Gaming consoles are subject to a 15% restocking fee if opened. Unopened units carry no restocking fee.",
        "context":  "Restocking Fees: 15% restocking fee applies to opened gaming hardware...",
        "follow_ups": [
            ("What counts as opened?",                 "Any item where the original factory seal has been broken is considered opened."),
            ("Is there a restocking fee for TVs?",     "There is no restocking fee for TVs returned within 30 days, opened or unopened."),
            ("Can the fee be waived?",                 "Restocking fees may be waived in cases of manufacturer defect or if the wrong item was shipped. Standard returns are subject to the policy."),
        ]
    },
    {
        "question": "How do I initiate a return for my order?",
        "answer":   "To initiate a return, visit your order history, select the item, and click 'Request Return'. You'll receive a prepaid label within 24 hours.",
        "context":  "Returns Process: Initiate via order history portal. Prepaid return label emailed within 24 hours...",
        "follow_ups": [
            ("I don't have an account, can I still return?", "Yes, you can initiate a return by contacting us with your order ID and the email used at checkout."),
            ("How do I pack the item?",                "Please pack the item in its original packaging if possible and include all accessories. Attach the prepaid label to the outside of the box."),
            ("When will I get my refund?",             "Refunds are processed within 3-5 business days of us receiving the returned item."),
        ]
    },
]

CHAT_TURNS = [
    {
        "question": "Hi, can you help me?",
        "answer":   "Of course! What can I help you with today?",
        "follow_ups": [
            ("I'm looking for a gift for a gamer.",    "Great choice! We have a wide range of gaming products. Are you looking for a console, controller, or accessories?"),
            ("I need help with my recent order.",      "I'd be happy to help. Could you share your order ID so I can look it up?"),
            ("Just browsing, thanks!",                 "No problem! Let me know if anything catches your eye."),
        ]
    },
    {
        "question": "Hello!",
        "answer":   "Hi there! How can I assist you today?",
        "follow_ups": [
            ("Do you have any sales going on?",        "Yes! We currently have a 20% discount on all gaming products and 15% off the BudgetSmart TV range."),
            ("I have a quick question about returns.", "Of course, I'm happy to help. What would you like to know?"),
            ("Never mind, I found what I needed.",     "Great! Feel free to come back if you have any other questions."),
        ]
    },
    {
        "question": "Thanks, that answered my question!",
        "answer":   "Happy to help! Let me know if anything else comes up.",
        "follow_ups": [
            ("Actually, one more thing — do you price match?", "Yes, we offer price matching on identical items sold by major retailers. Send us the competitor's listing and we'll review it."),
            ("You've been really helpful, thank you.", "It's my pleasure! Have a great day."),
        ]
    },
    {
        "question": "Great, I'll go ahead and place the order.",
        "answer":   "Sounds great! Feel free to reach out if you need anything after your order arrives.",
        "follow_ups": [
            ("How will I know when it ships?",         "You'll receive a shipping confirmation email with a tracking number as soon as your order is dispatched."),
            ("Can I add something to the order?",      "Unfortunately orders can't be modified once placed, but you're welcome to place a second order and we can look into combining shipping."),
        ]
    },
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
    avg_helpfulness = sum(turn_scores) / len(turn_scores) if turn_scores else 1.0
    if avg_helpfulness < 0.4:
        base = min(1.0, base + 0.3)
    return round(base, 2)

# ──────────────────────────────────────────────────────────────────────────────
# TRACE BUILDER
# question and answer are always selected together from the same turn dict
# so they are guaranteed to match. Returns (question, answer) so the main
# loop can build realistic chat_history for the next turn.
# ──────────────────────────────────────────────────────────────────────────────
def log_trace(thread_id, turn_index, question, answer, route, chat_history, trace_start, sql=None, context=None):
    total_dur = random.uniform(1.2, 9.0)
    t         = trace_start
    
    # Ensure timestamp is timezone-aware for proper Opik dashboard grouping
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    
    # Generate trace ID with historical timestamp - CRITICAL for dashboard date grouping
    trace_id = id_helpers.generate_id(timestamp=t)

    # ── Root trace ─────────────────────────────────────────────────────────
    trace = client.trace(
        id           = trace_id,  # Use generated ID with historical timestamp
        name         = "OhmBot_Support",
        project_name = PROJECT_NAME,
        input        = {"user": question},
        output       = None,
        tags         = ["production", route.lower()],
        metadata     = {
            "environment" : "production",
            "session_id"  : thread_id,
            "turn_index"  : turn_index,
            "chat_history": chat_history,
            "_opik_graph_definition": {"format": "mermaid", "data": MERMAID_GRAPH},
        },
        thread_id    = thread_id,
        start_time   = t,
    )

    # ── Router span ────────────────────────────────────────────────────────
    router_dur  = random.uniform(0.3, 0.9)
    router_span_start = t
    router_span_id = id_helpers.generate_id(timestamp=router_span_start)
    router_span = trace.span(
        id         = router_span_id,  # Use generated ID with historical timestamp
        name       = "route_user_request",
        type       = "llm",
        model      = MODEL,
        provider   = "openai",
        input      = {"messages": [{"role": "user", "content": f"Classify: {question}"}]},
        output     = {"choices": [{"message": {"content": route}}]},
        usage      = make_usage(30, 120, 1, 5),
        start_time = router_span_start,
        end_time   = router_span_start + timedelta(seconds=router_dur),
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
    if route == "DATABASE":
        sql_gen_dur = random.uniform(0.8, 2.5)
        sql_gen_start = t
        sql_gen_id = id_helpers.generate_id(timestamp=sql_gen_start)
        sql_gen = trace.span(
            id         = sql_gen_id,
            name       = "SQL_Generation_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"tool_call": {"name": "run_sql_query", "arguments": {"query": sql}}},
            usage      = make_usage(150, 400, 20, 60),
            start_time = sql_gen_start,
            end_time   = sql_gen_start + timedelta(seconds=sql_gen_dur),
        )
        sql_gen.end()
        t += timedelta(seconds=sql_gen_dur)

        tool_dur  = random.uniform(0.05, 0.3)
        tool_span_start = t
        tool_span_id = id_helpers.generate_id(timestamp=tool_span_start)
        tool_span = trace.span(
            id         = tool_span_id,
            name       = "run_sql_query",
            type       = "tool",
            input      = {"query": sql},
            output     = {"result": "| col1 | col2 |\n|------|------|\n| val1 | val2 |"},
            start_time = tool_span_start,
            end_time   = tool_span_start + timedelta(seconds=tool_dur),
            metadata   = {"database": "ohm_sweet_ohm.db"},
        )
        tool_span.end()
        t += timedelta(seconds=tool_dur)

        final_dur  = random.uniform(0.5, 1.5)
        final_span_start = t
        final_span_id = id_helpers.generate_id(timestamp=final_span_start)
        final_span = trace.span(
            id         = final_span_id,
            name       = "SQL_Final_Answer_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(200, 500, 40, 150),
            start_time = final_span_start,
            end_time   = final_span_start + timedelta(seconds=final_dur),
        )
        final_span.end()

    elif route == "POLICY":
        rag_gen_dur = random.uniform(0.6, 1.8)
        rag_gen_start = t
        rag_gen_id = id_helpers.generate_id(timestamp=rag_gen_start)
        rag_gen = trace.span(
            id         = rag_gen_id,
            name       = "RAG_Query_Generation",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"tool_call": {"name": "look_up_policy", "arguments": {"query": question}}},
            usage      = make_usage(100, 300, 10, 40),
            start_time = rag_gen_start,
            end_time   = rag_gen_start + timedelta(seconds=rag_gen_dur),
        )
        rag_gen.end()
        t += timedelta(seconds=rag_gen_dur)

        retrieval_dur  = random.uniform(0.1, 0.5)
        retrieval_span_start = t
        retrieval_span_id = id_helpers.generate_id(timestamp=retrieval_span_start)
        retrieval_span = trace.span(
            id         = retrieval_span_id,
            name       = "look_up_policy",
            type       = "tool",
            input      = {"query": question},
            output     = {"chunks": [context], "n_results": random.randint(1, 3)},
            start_time = retrieval_span_start,
            end_time   = retrieval_span_start + timedelta(seconds=retrieval_dur),
            metadata   = {"index": "faq.txt"},
        )
        retrieval_span.end()
        t += timedelta(seconds=retrieval_dur)

        final_dur  = random.uniform(0.6, 2.0)
        final_span_start = t
        final_span_id = id_helpers.generate_id(timestamp=final_span_start)
        final_span = trace.span(
            id         = final_span_id,
            name       = "RAG_Final_Answer_Step",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [
                {"role": "system", "content": "You are a policy assistant. Use the handbook."},
                {"role": "tool",   "content": context},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(250, 600, 50, 200),
            start_time = final_span_start,
            end_time   = final_span_start + timedelta(seconds=final_dur),
        )
        final_span.end()

    else:  # CHAT
        chat_dur  = random.uniform(0.4, 1.2)
        chat_span_start = t
        chat_span_id = id_helpers.generate_id(timestamp=chat_span_start)
        chat_span = trace.span(
            id         = chat_span_id,
            name       = "run_chat_workflow",
            type       = "llm", model=MODEL, provider="openai",
            input      = {"messages": [
                {"role": "system", "content": "You are a helpful customer support assistant."},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(50, 150, 20, 80),
            start_time = chat_span_start,
            end_time   = chat_span_start + timedelta(seconds=chat_dur),
        )
        chat_span.end()

    # ── Close root trace ───────────────────────────────────────────────────
    # Ensure end_time is also timezone-aware
    trace_end = trace_start + timedelta(seconds=total_dur)
    if trace_end.tzinfo is None:
        trace_end = trace_end.replace(tzinfo=timezone.utc)
    
    trace.end(
        end_time = trace_end,
        output   = {"assistant": answer},
    )
    trace.log_feedback_score(
        name   = "answer_helpfulness",
        value  = helpfulness_score(),
        reason = "Synthetic user rating",
    )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# Each thread picks one turn dict (first turn) then uses that dict's follow_ups
# for subsequent turns — so every conversation stays on topic.
# ──────────────────────────────────────────────────────────────────────────────
now = datetime.now(timezone.utc)
total_traces = 0
thread_feedback_scores = []  # Batch feedback scores for efficiency

for thread_idx in tqdm(range(NUM_THREADS), desc="Seeding OhmBot traces", unit="thread"):
    thread_id    = f"session-{uuid.uuid4().hex[:12]}"
    num_turns    = random.choices([1, 2, 3, 4], weights=[35, 35, 20, 10])[0]
    days_ago     = random.betavariate(2, 5) * DAYS_BACK
    # Calculate historical timestamp - ensure it's timezone-aware
    thread_start = now - timedelta(days=days_ago, minutes=random.randint(0, 120))
    if thread_start.tzinfo is None:
        thread_start = thread_start.replace(tzinfo=timezone.utc)

    # Pick route and a matching turn dict for this whole thread
    route = random.choices(["DATABASE", "POLICY", "CHAT"], weights=ROUTE_WEIGHTS)[0]
    if route == "DATABASE":
        turn_dict = random.choice(DATABASE_TURNS)
    elif route == "POLICY":
        turn_dict = random.choice(POLICY_TURNS)
    else:
        turn_dict = random.choice(CHAT_TURNS)

    # Shuffle follow-ups so repeated threads with same dict feel different
    follow_ups = list(turn_dict.get("follow_ups", []))
    random.shuffle(follow_ups)

    chat_history = []
    turn_scores  = []

    for turn in range(num_turns):
        turn_start = thread_start + timedelta(minutes=turn * random.uniform(2, 8))

        if turn == 0:
            # First turn: use the primary question/answer from the turn dict
            question = turn_dict["question"]
            answer   = turn_dict["answer"]
        elif follow_ups:
            # Subsequent turns: use a follow-up from the same topic
            question, answer = follow_ups.pop(0)
            # Follow-ups are conversational — route them through CHAT workflow
            # unless the thread is DATABASE/POLICY and it's a content follow-up
            route = route if turn == 1 else "CHAT"
        else:
            # Ran out of follow-ups — close the thread naturally
            question = "Thanks, that's all I needed!"
            answer   = "Happy to help! Don't hesitate to reach out if anything comes up."
            route    = "CHAT"

        log_trace(
            thread_id    = thread_id,
            turn_index   = turn,
            question     = question,
            answer       = answer,
            route        = route,
            chat_history = chat_history,
            trace_start  = turn_start,
            sql          = turn_dict.get("sql"),
            context      = turn_dict.get("context"),
        )

        turn_scores.append(helpfulness_score())
        chat_history.append({"role": "user",      "content": question})
        chat_history.append({"role": "assistant",  "content": answer})
        total_traces += 1

    # ── Collect thread-level frustration score for batch logging ────────────
    thread_feedback_scores.append({
        "id"    : thread_id,
        "name"  : "user_frustration",
        "value" : frustration_score(turn_scores),
        "reason": f"{num_turns} turn(s), avg helpfulness {sum(turn_scores)/len(turn_scores):.2f}",
    })

# All traces are now created and queued in Opik's internal buffer
# Opik will handle sending them in the background, respecting rate limits
print(f"\n📤 Created {total_traces} traces. Initiating flush to Opik...")

# Flush with timeout to avoid blocking the notebook for too long
# Opik will continue sending traces in the background even if flush times out
def flush_with_timeout(timeout_seconds=30):
    """Flush with a timeout - if it takes too long, let Opik continue in background."""
    def timeout_handler(signum, frame):
        raise TimeoutError("Flush timed out")
    
    # Set up timeout (Unix only - Windows will skip timeout)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    
    try:
        client.flush()
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel timeout
        return True
    except (TimeoutError, KeyboardInterrupt):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel timeout
        return False
    except Exception:
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel timeout
        return False

# Try to flush, but don't block for more than 30 seconds
flushed = flush_with_timeout(timeout_seconds=30)

if not flushed:
    print("⏱️  Flush timed out after 30 seconds. Opik will continue sending traces in the background.")
    print("   Your traces will appear in Opik shortly - no action needed!")
else:
    print("✅ Flush completed successfully.")

# Batch log all feedback scores at once
if thread_feedback_scores:
    try:
        client.log_threads_feedback_scores(scores=thread_feedback_scores)
    except Exception:
        pass

print(f"✅ Seeded {total_traces} traces across {NUM_THREADS} threads into '{PROJECT_NAME}'.")
print("💡 Note: If flush timed out, traces are still being sent by Opik in the background.")
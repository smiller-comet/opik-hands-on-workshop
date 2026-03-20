"""
seed_data.py

Populates the Opik project with 30 days of synthetic production traces in two
phases to illustrate prompt improvement over time:

  Phase 1 (days 30–15 ago):  Router Prompt V1 — misroutes promotions/deals to
                              POLICY and bare order IDs to CHAT. ~60% routing
                              accuracy, lower helpfulness scores.
                              Traces tagged prompt_version:v1.

  Phase 2 (days 14–0 ago):   Router Prompt V2 — correct routing for all query
                              types including promotions and order follow-ups.
                              ~95% routing accuracy, higher helpfulness scores.
                              Traces tagged prompt_version:v2.

Both prompt versions are registered in the Opik Prompt Library so the exact
template used for each historical trace is inspectable.

Note on historical timestamps:
Trace and span IDs are generated with id_helpers.generate_id(timestamp=t) so
traces appear under their historical dates in Opik dashboards, not the
ingestion date.
"""

import os
import sys
import random
import uuid
from datetime import datetime, timedelta, timezone

import opik
from opik import id_helpers

# ── tqdm is available in Colab; fall back gracefully if not ──────────────────
try:
    from tqdm.auto import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        print(kwargs.get("desc", ""), "...")
        return iterable


# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_NAME  = os.environ.get("OPIK_PROJECT_NAME", "Ohm Sweet Ohm Support Agent")
NUM_THREADS   = 100
DAYS_BACK     = 30
CUTOFF_DAYS   = 15   # days ago where V1 → V2 transition occurred
MODEL         = "gpt-4o"

# V1 misrouting rate in phase 1: 40% of phase-1 threads use a failure turn
V1_FAILURE_RATE = 0.40


# ──────────────────────────────────────────────────────────────────────────────
# PROMPTS
# Both versions are registered in the Opik Prompt Library below.
# ──────────────────────────────────────────────────────────────────────────────

ROUTER_PROMPT_V1 = """You are a router. Classify the user question:
1. DATABASE: Product stock, inventory, prices. SPECIFIC ORDER STATUS with order ID.
2. POLICY: Return policy, warranty, shipping info, FAQ.
3. CHAT: Greetings, "thank you", casual chatter.

Output ONLY the category name.
Question: {user_question}"""

ROUTER_PROMPT_V2 = """You are a router. Classify the user question:
1. DATABASE:
   - Product stock, inventory, prices, store info.
   - PROMOTIONS, DISCOUNTS, DEALS, SALES, COUPONS (any questions about special offers or pricing).
   - SPECIFIC ORDER STATUS, "Where is my order?", "Track my package".
2. POLICY:
   - General return policy, warranty info.
   - GENERAL shipping times/costs (NOT specific order status).
   - Company FAQ.
3. CHAT:
   - Greetings, "thank you", "no", "yes", or casual chatter.

Output ONLY the category name.
Question: {user_question}"""

SQL_SYSTEM_PROMPT = """You are a SQL data assistant.
1. When searching for products, use LIKE patterns on the 'name' or 'description' field.
2. For promotions/deals, search the 'promotions' table description field.
3. For ORDER status, you MUST have the order_id. If missing, ask the user."""

CHAT_SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for Ohm Sweet Ohm. Be polite and concise."
)

RAG_SYSTEM_PROMPT = "You are a policy assistant. Use the handbook to answer questions."


# ──────────────────────────────────────────────────────────────────────────────
# OPIK SETUP
# ──────────────────────────────────────────────────────────────────────────────
opik.configure(use_local=False)
client = opik.Opik(project_name=PROJECT_NAME)


# ── Register both router prompt versions in the Opik Prompt Library ───────────
# Calling opik.Prompt with the same name but different content creates a new
# version. V1 is registered first (version 1), V2 second (version 2).
# If the same content already exists it returns the existing version (idempotent).
print("📝 Registering prompt versions in Opik Prompt Library...")
try:
    _router_v1_obj = opik.Prompt(name="Router Prompt", prompt=ROUTER_PROMPT_V1)
    _router_v2_obj = opik.Prompt(name="Router Prompt", prompt=ROUTER_PROMPT_V2)
    print(
        f"   ✓ Router Prompt v{_router_v1_obj.version} (V1) "
        f"and v{_router_v2_obj.version} (V2) ready."
    )
except Exception as exc:
    print(f"   ⚠️  Prompt Library registration failed: {exc}. Continuing without linking.")
    _router_v1_obj = None
    _router_v2_obj = None


# ── Skip guard ────────────────────────────────────────────────────────────────
try:
    existing = client.search_traces(project_name=PROJECT_NAME, max_results=1)
    if existing:
        print("✅ Demo data already exists — skipping seed.")
        sys.exit(0)
except Exception:
    pass


# ──────────────────────────────────────────────────────────────────────────────
# CONVERSATION DATA
# ──────────────────────────────────────────────────────────────────────────────

DATABASE_TURNS = [
    {
        "question": "How many AirStream Wireless Earbuds do you have in stock?",
        "answer":   "The AirStream Wireless Earbuds (AUDIO-103) currently have 47 units in stock.",
        "sql":      "SELECT stock_level FROM store_inventory si JOIN products p ON si.product_id = p.product_id WHERE p.name LIKE '%AirStream%'",
        "follow_ups": [
            ("Are they available in white?",          "Yes, the AirStream Wireless Earbuds are available in white, black, and navy blue."),
            ("Great, what's the price?",              "The AirStream Wireless Earbuds are priced at $79.99."),
            ("Do they come with a warranty?",         "Yes, all Ohm audio products include a 1-year limited warranty."),
        ],
    },
    {
        "question": "Is the NexGen Pro Gaming Console available?",
        "answer":   "Yes, the NexGen Pro Gaming Console (GAME-1101) is available with 12 units remaining.",
        "sql":      "SELECT in_stock, name FROM products WHERE product_id = 'GAME-1101'",
        "follow_ups": [
            ("How much does it cost?",                "The NexGen Pro Gaming Console is priced at $499.99."),
            ("Does it come with any games?",          "The NexGen Pro Gaming Console comes bundled with one controller and a 1-month game pass."),
            ("Can I pick it up in store?",            "Yes, you can reserve it for in-store pickup. Which city are you located in?"),
        ],
    },
    {
        "question": "Do you have the CrystalView 4K Smart TV in 65 inch?",
        "answer":   "The CrystalView 4K Smart TV 65\" (TV-1301-65) has 8 units in stock.",
        "sql":      "SELECT in_stock FROM products WHERE product_id = 'TV-1301-65'",
        "follow_ups": [
            ("What's the price on that?",             "The CrystalView 4K Smart TV 65\" is priced at $1,199.99."),
            ("Is there a wall mount included?",       "The TV does not include a wall mount, but we carry compatible mounts starting at $39.99."),
            ("What's the return policy on TVs?",      "TVs can be returned within 30 days. Units 65\" and larger require a scheduled pickup."),
        ],
    },
    {
        "question": "What's the stock level for the PlayStation 5?",
        "answer":   "The PlayStation 5 (GAME-1102) is currently out of stock. We expect restocking next week.",
        "sql":      "SELECT in_stock FROM products WHERE product_id = 'GAME-1102'",
        "follow_ups": [
            ("Can I be notified when it's back?",     "Yes! You can sign up for a restock alert on the product page and we'll email you immediately."),
            ("Do you have any PS5 bundles?",          "We currently have a PS5 + extra controller bundle reserved for the restock. Would you like to be added to the waitlist?"),
            ("What about the NexGen Pro instead?",    "The NexGen Pro Gaming Console (GAME-1101) is available now with 12 units in stock at $499.99."),
        ],
    },
    {
        "question": "How much does the NexusWave Pro Headphones cost?",
        "answer":   "The NexusWave Pro Headphones (AUDIO-101) are priced at $349.99.",
        "sql":      "SELECT price FROM products WHERE product_id = 'AUDIO-101'",
        "follow_ups": [
            ("Is there any discount available?",      "There is currently a $30 promotional discount on the NexusWave Pro, bringing it to $319.99."),
            ("How do they compare to the SonicBlast?", "The NexusWave Pro offers active noise cancellation and 30-hour battery life. The SonicBlast is studio-focused with a flatter sound profile."),
            ("What's the return policy if I don't like them?", "Headphones can be returned within 30 days in original condition with receipt."),
        ],
    },
    {
        "question": "Where is my order? My order ID is ORD-10482.",
        "answer":   "Order ORD-10482 is currently in transit and estimated to arrive within 2 business days.",
        "sql":      "SELECT status, current_location, days_since_order FROM orders WHERE order_id = 'ORD-10482'",
        "follow_ups": [
            ("Which carrier is handling it?",         "Order ORD-10482 is being shipped via UPS. Your tracking number is 1Z999AA10123456784."),
            ("Can I change the delivery address?",    "Address changes are possible if the order hasn't reached the final sorting facility. I'll flag this for our shipping team."),
            ("What if it doesn't arrive on time?",    "If your order is delayed past the estimated delivery date, contact us and we'll initiate an investigation with the carrier."),
        ],
    },
    {
        "question": "Can you check the status of order ORD-77210?",
        "answer":   "Order ORD-77210 shipped yesterday via FedEx. Tracking number: FX-9921047.",
        "sql":      "SELECT status, current_location FROM orders WHERE order_id = 'ORD-77210'",
        "follow_ups": [
            ("When is the expected delivery?",        "Based on the FedEx tracking, ORD-77210 is expected to arrive this Thursday."),
            ("Can I see what's in that order?",       "Order ORD-77210 contains: 1x NexusWave Pro Headphones and 1x MultiCharge Cable Set."),
            ("Thanks, that's all I needed.",          "Great! Don't hesitate to reach out if anything else comes up."),
        ],
    },
    {
        "question": "Are there any deals on gaming products right now?",
        "answer":   "Yes! There's currently a 20% discount on all gaming products through end of month.",
        "sql":      "SELECT description, discount_percent FROM promotions WHERE description LIKE '%gaming%' OR description LIKE '%game%'",
        "follow_ups": [
            ("Does that include the NexGen Pro Console?", "Yes, the NexGen Pro Gaming Console is included — 20% off brings it to $399.99."),
            ("What about the ProGamer Controller?",   "Yes, the ProGamer Controller is also 20% off, down to $55.99 from $69.99."),
            ("How long is the sale running?",         "The gaming promotion runs through the end of this month."),
        ],
    },
    {
        "question": "What is the price of the BudgetSmart LED TV 55 inch?",
        "answer":   "The BudgetSmart LED TV 55\" (TV-1303-55) is priced at $399.99.",
        "sql":      "SELECT price FROM products WHERE product_id = 'TV-1303-55'",
        "follow_ups": [
            ("Is there a 65 inch version?",           "Yes, the BudgetSmart LED TV 65\" (TV-1303-65) is available at $549.99."),
            ("Does it support 4K?",                   "The BudgetSmart LED TV supports 4K resolution with HDR and built-in smart TV features."),
            ("Any promotions on it right now?",       "The BudgetSmart LED TV range has a 15% promotional discount running this week."),
        ],
    },
]

POLICY_TURNS = [
    {
        "question": "What is your return policy?",
        "answer":   "We accept returns within 30 days of purchase with proof of receipt for all items in original condition.",
        "context":  "Return Policy: All items eligible for return within 30 days in original condition with receipt.",
        "follow_ups": [
            ("What if I lost my receipt?",            "Without a receipt, we can look up your purchase using the order ID or the email address used at checkout."),
            ("Can I return an opened item?",          "Opened items are returnable within 30 days. Some categories like gaming hardware have a 15% restocking fee if opened."),
            ("How long does the refund take?",        "Refunds are processed within 3-5 business days after we receive the item."),
        ],
    },
    {
        "question": "How long does standard shipping take?",
        "answer":   "Standard shipping takes 5–7 business days. Express shipping (2-day) is available at checkout.",
        "context":  "Shipping Policy: Standard 5-7 business days. Express 2-day available.",
        "follow_ups": [
            ("Is there free shipping?",               "Yes, standard shipping is free on all orders over $50."),
            ("Can I upgrade to express after ordering?", "Shipping upgrades are possible if the order hasn't been picked up by the carrier yet."),
            ("Do you ship on weekends?",              "Orders placed Friday after 3pm through Sunday will begin processing on Monday."),
        ],
    },
    {
        "question": "Do you offer a warranty on electronics?",
        "answer":   "All electronics carry a 1-year limited manufacturer warranty covering defects in materials and workmanship.",
        "context":  "Warranty Policy: 1-year limited warranty on all electronics.",
        "follow_ups": [
            ("Does it cover accidental damage?",      "The standard warranty does not cover accidental damage. We offer an extended protection plan that covers it for an additional fee."),
            ("How do I make a warranty claim?",       "Contact our support team with your order ID and a description of the issue. We'll guide you through the process."),
            ("Can I extend the warranty?",            "Yes, we offer 2-year and 3-year extended protection plans available for purchase within 30 days of your order."),
        ],
    },
    {
        "question": "What happens if my item arrives damaged?",
        "answer":   "If your item arrives damaged, contact us within 48 hours with a photo and we'll send a replacement or issue a full refund.",
        "context":  "Damaged Items: Customer must report within 48 hours with photographic evidence.",
        "follow_ups": [
            ("Do I need to return the damaged item?", "For most damaged items, we don't require a return — we'll send a replacement after verifying the damage photo."),
            ("What if it's been more than 48 hours?", "We recommend contacting us as soon as possible. Late reports are reviewed on a case-by-case basis."),
            ("How quickly will the replacement arrive?", "Replacement orders are prioritized and typically shipped within 24 hours via express delivery."),
        ],
    },
    {
        "question": "Do you ship internationally?",
        "answer":   "We ship to over 40 countries. International delivery takes 10–14 business days and customs fees may apply.",
        "context":  "International Shipping: Available to 40+ countries. 10-14 business day delivery.",
        "follow_ups": [
            ("Which countries do you ship to?",       "We ship to most countries in Europe, Asia-Pacific, and North America. You can see the full list at checkout."),
            ("Who pays the customs fees?",            "Customs and import duties are the responsibility of the recipient and vary by country."),
            ("Is express international shipping available?", "We offer international express shipping (5-7 days) to select countries for an additional fee."),
        ],
    },
    {
        "question": "Is there a restocking fee for returned gaming consoles?",
        "answer":   "Gaming consoles are subject to a 15% restocking fee if opened. Unopened units carry no restocking fee.",
        "context":  "Restocking Fees: 15% restocking fee applies to opened gaming hardware.",
        "follow_ups": [
            ("What counts as opened?",                "Any item where the original factory seal has been broken is considered opened."),
            ("Is there a restocking fee for TVs?",    "There is no restocking fee for TVs returned within 30 days, opened or unopened."),
            ("Can the fee be waived?",                "Restocking fees may be waived in cases of manufacturer defect or if the wrong item was shipped."),
        ],
    },
    {
        "question": "How do I initiate a return for my order?",
        "answer":   "To initiate a return, visit your order history, select the item, and click 'Request Return'. You'll receive a prepaid label within 24 hours.",
        "context":  "Returns Process: Initiate via order history portal. Prepaid return label emailed within 24 hours.",
        "follow_ups": [
            ("I don't have an account, can I still return?", "Yes, contact us with your order ID and the email used at checkout."),
            ("How do I pack the item?",               "Pack in original packaging if possible, include all accessories, and attach the prepaid label to the outside."),
            ("When will I get my refund?",            "Refunds are processed within 3-5 business days of us receiving the returned item."),
        ],
    },
]

CHAT_TURNS = [
    {
        "question": "Hi, can you help me?",
        "answer":   "Of course! What can I help you with today?",
        "follow_ups": [
            ("I'm looking for a gift for a gamer.",   "Great choice! We have a wide range of gaming products. Are you looking for a console, controller, or accessories?"),
            ("I need help with my recent order.",     "I'd be happy to help. Could you share your order ID so I can look it up?"),
            ("Just browsing, thanks!",                "No problem! Let me know if anything catches your eye."),
        ],
    },
    {
        "question": "Hello!",
        "answer":   "Hi there! How can I assist you today?",
        "follow_ups": [
            ("Do you have any sales going on?",       "Yes! We currently have a 20% discount on all gaming products and 15% off the BudgetSmart TV range."),
            ("I have a quick question about returns.", "Of course, I'm happy to help. What would you like to know?"),
            ("Never mind, I found what I needed.",    "Great! Feel free to come back if you have any other questions."),
        ],
    },
    {
        "question": "Thanks, that answered my question!",
        "answer":   "Happy to help! Let me know if anything else comes up.",
        "follow_ups": [
            ("Actually, one more thing — do you price match?", "Yes, we offer price matching on identical items sold by major retailers. Send us the competitor's listing and we'll review it."),
            ("You've been really helpful, thank you.", "It's my pleasure! Have a great day."),
        ],
    },
    {
        "question": "Great, I'll go ahead and place the order.",
        "answer":   "Sounds great! Feel free to reach out if you need anything after your order arrives.",
        "follow_ups": [
            ("How will I know when it ships?",        "You'll receive a shipping confirmation email with a tracking number as soon as your order is dispatched."),
            ("Can I add something to the order?",     "Unfortunately orders can't be modified once placed, but you're welcome to place a second order and we can look into combining shipping."),
        ],
    },
]

# ── V1 failure turns ───────────────────────────────────────────────────────────
# These are DATABASE questions that V1 misroutes to POLICY or CHAT because the
# V1 router prompt doesn't include promotions/deals in DATABASE or handle bare
# order IDs as follow-ups. Used only in phase 1 traces.
V1_FAILURE_TURNS = [
    {
        "question":   "Are there any deals on gaming products right now?",
        "answer":     "I can help with policy questions, but I don't have information about current promotions or deals. Please check our website or contact our sales team for the latest offers.",
        "routed_as":  "POLICY",   # V1 misroutes — should be DATABASE
        "true_route": "DATABASE",
        "context":    "Return Policy: All items eligible for return within 30 days in original condition with receipt.",
        "follow_ups": [
            ("Do you have any coupons?",              "For coupon information, I'd recommend checking our website's promotions page — I primarily handle policy and FAQ questions."),
            ("Any discount for first-time buyers?",   "I'm not able to access promotional pricing. Our policy team can help with returns, warranties, and shipping questions."),
        ],
    },
    {
        "question":   "What promotions are running this week?",
        "answer":     "I handle policy and FAQ questions. For current promotions and deals, please visit our website or speak to our sales team directly.",
        "routed_as":  "POLICY",
        "true_route": "DATABASE",
        "context":    "Warranty Policy: 1-year limited warranty on all electronics covering defects in materials and workmanship.",
        "follow_ups": [
            ("Is there a sale on TVs?",               "TV pricing and promotions aren't something I can access from the policy handbook. Please check our website for current deals."),
            ("Any Black Friday deals?",               "Seasonal promotions are managed by our marketing team. I can help with returns, warranties, or shipping information instead."),
        ],
    },
    {
        "question":   "Do you have any discounts on headphones?",
        "answer":     "For current pricing and discounts, I'd suggest checking our website directly. I'm set up to help with policy questions like returns, warranties, and shipping.",
        "routed_as":  "POLICY",
        "true_route": "DATABASE",
        "context":    "Shipping Policy: Standard shipping takes 5-7 business days. Express 2-day shipping is available.",
        "follow_ups": [
            ("What's the best headphone deal you have?", "I'm not able to pull up current deals or pricing. Our sales team would be best placed to help with that."),
            ("Are there any bundle deals?",           "Bundle promotions aren't covered in the policy handbook I have access to. Please visit our website for current bundle offers."),
        ],
    },
    {
        "question":   "ORD-10482",
        "answer":     "I'm not sure what you're asking. Could you clarify what you need help with today?",
        "routed_as":  "CHAT",     # V1 misroutes bare order ID — should be DATABASE
        "true_route": "DATABASE",
        "follow_ups": [
            ("I just want to know where my order is", "I understand you're looking for order information, but I wasn't able to interpret your previous message. Could you try: 'Where is my order ORD-10482?'"),
            ("This is frustrating, I just need my order status", "I apologize for the confusion. For order status, please contact our support team directly with your order ID and we'll look it up right away."),
        ],
    },
    {
        "question":   "Any sales on right now?",
        "answer":     "I'm focused on helping with policy questions like returns and warranties. For sales and promotions, our website is the best place to check.",
        "routed_as":  "POLICY",
        "true_route": "DATABASE",
        "context":    "Warranty Policy: Extended protection plans available for purchase within 30 days of order.",
        "follow_ups": [
            ("Even just a small discount?",           "I'm not set up to access pricing or promotions — I can only help with policy and FAQ questions."),
            ("Who should I talk to about deals?",     "Our sales team can help with promotions. You can reach them via live chat on our website or by calling our support line."),
        ],
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


def helpfulness_score(phase, is_misrouted=False):
    """Return a synthetic helpfulness score weighted by phase and routing outcome."""
    if is_misrouted:
        # Misrouted responses are almost always unhelpful
        return random.choices([0.25, 0.0], weights=[35, 65])[0]
    if phase == 1:
        # V1 era — more variance, skewed lower
        return random.choices([1.0, 0.75, 0.5, 0.25, 0.0], weights=[20, 25, 25, 18, 12])[0]
    # V2 era — mostly helpful
    return random.choices([1.0, 0.75, 0.5, 0.25, 0.0], weights=[55, 30, 10, 4, 1])[0]


def frustration_score(turn_scores):
    base = random.choices([0.0, 0.1, 0.3, 0.6, 0.9, 1.0], weights=[35, 25, 20, 10, 7, 3])[0]
    avg_helpfulness = sum(turn_scores) / len(turn_scores) if turn_scores else 1.0
    if avg_helpfulness < 0.4:
        base = min(1.0, base + 0.3)
    return round(base, 2)


# ──────────────────────────────────────────────────────────────────────────────
# TRACE BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def log_trace(
    thread_id,
    question,
    answer,
    route,
    trace_start,
    phase,
    prompt_obj,
    routing_correct,
    is_misrouted=False,
    sql=None,
    context=None,
):
    """Log a single trace with all spans to Opik."""
    total_dur = random.uniform(1.2, 9.0)
    t = trace_start
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)

    prompt_version = prompt_obj.version if prompt_obj else ("1" if phase == 1 else "2")
    prompt_version_tag = f"prompt_version:v{phase}"

    trace_id = id_helpers.generate_id(timestamp=t)
    trace = client.trace(
        id           = trace_id,
        name         = "OhmSweetOhm_Agent",
        project_name = PROJECT_NAME,
        input        = {"question": question},
        output       = None,
        tags         = ["production", route.lower(), prompt_version_tag],
        metadata     = {
            "_opik_graph_definition": {"format": "mermaid", "data": MERMAID_GRAPH},
            "prompt_name":    "Router Prompt",
            "prompt_version": prompt_version,
            "phase":          phase,
        },
        thread_id    = thread_id,
        start_time   = t,
    )

    # ── Router span ───────────────────────────────────────────────────────────
    router_prompt_text = ROUTER_PROMPT_V1 if phase == 1 else ROUTER_PROMPT_V2
    router_dur = random.uniform(0.3, 0.9)
    router_start = t
    router_span = trace.span(
        id         = id_helpers.generate_id(timestamp=router_start),
        name       = "route_user_request",
        type       = "llm",
        model      = MODEL,
        provider   = "openai",
        input      = {"messages": [
            {"role": "user", "content": router_prompt_text.format(user_question=question)},
        ]},
        output     = {"choices": [{"message": {"content": route}}]},
        usage      = make_usage(30, 120, 1, 5),
        metadata   = {"prompt_name": "Router Prompt", "prompt_version": prompt_version},
        start_time = router_start,
        end_time   = router_start + timedelta(seconds=router_dur),
    )
    router_span.end()
    t += timedelta(seconds=router_dur)

    # ── Workflow branch ───────────────────────────────────────────────────────
    if route == "DATABASE":
        sql_gen_dur   = random.uniform(0.8, 2.5)
        sql_gen_start = t
        sql_gen = trace.span(
            id         = id_helpers.generate_id(timestamp=sql_gen_start),
            name       = "SQL_Generation_Step",
            type       = "llm",
            model      = MODEL,
            provider   = "openai",
            input      = {"messages": [
                {"role": "system", "content": SQL_SYSTEM_PROMPT},
                {"role": "user",   "content": question},
            ]},
            output     = {"tool_call": {"name": "run_sql_query", "arguments": {"query": sql or ""}}},
            usage      = make_usage(150, 400, 20, 60),
            start_time = sql_gen_start,
            end_time   = sql_gen_start + timedelta(seconds=sql_gen_dur),
        )
        sql_gen.end()
        t += timedelta(seconds=sql_gen_dur)

        tool_dur   = random.uniform(0.05, 0.3)
        tool_start = t
        tool_span = trace.span(
            id         = id_helpers.generate_id(timestamp=tool_start),
            name       = "run_sql_query",
            type       = "tool",
            input      = {"query": sql or ""},
            output     = {"result": "| product | stock |\n|---------|-------|\n| item    | 47    |"},
            start_time = tool_start,
            end_time   = tool_start + timedelta(seconds=tool_dur),
        )
        tool_span.end()
        t += timedelta(seconds=tool_dur)

        final_dur   = random.uniform(0.5, 1.5)
        final_start = t
        final_span = trace.span(
            id         = id_helpers.generate_id(timestamp=final_start),
            name       = "SQL_Final_Answer_Step",
            type       = "llm",
            model      = MODEL,
            provider   = "openai",
            input      = {"messages": [{"role": "user", "content": question}]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(200, 500, 40, 150),
            start_time = final_start,
            end_time   = final_start + timedelta(seconds=final_dur),
        )
        final_span.end()

    elif route == "POLICY":
        rag_gen_dur   = random.uniform(0.6, 1.8)
        rag_gen_start = t
        rag_gen = trace.span(
            id         = id_helpers.generate_id(timestamp=rag_gen_start),
            name       = "RAG_Query_Generation",
            type       = "llm",
            model      = MODEL,
            provider   = "openai",
            input      = {"messages": [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user",   "content": question},
            ]},
            output     = {"tool_call": {"name": "look_up_policy", "arguments": {"query": question}}},
            usage      = make_usage(100, 300, 10, 40),
            start_time = rag_gen_start,
            end_time   = rag_gen_start + timedelta(seconds=rag_gen_dur),
        )
        rag_gen.end()
        t += timedelta(seconds=rag_gen_dur)

        ret_dur   = random.uniform(0.1, 0.5)
        ret_start = t
        ret_span = trace.span(
            id         = id_helpers.generate_id(timestamp=ret_start),
            name       = "look_up_policy",
            type       = "tool",
            input      = {"query": question},
            output     = {"chunks": [context or ""], "n_results": random.randint(1, 3)},
            start_time = ret_start,
            end_time   = ret_start + timedelta(seconds=ret_dur),
        )
        ret_span.end()
        t += timedelta(seconds=ret_dur)

        final_dur   = random.uniform(0.6, 2.0)
        final_start = t
        final_span = trace.span(
            id         = id_helpers.generate_id(timestamp=final_start),
            name       = "RAG_Final_Answer_Step",
            type       = "llm",
            model      = MODEL,
            provider   = "openai",
            input      = {"messages": [
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "tool",   "content": context or ""},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(250, 600, 50, 200),
            start_time = final_start,
            end_time   = final_start + timedelta(seconds=final_dur),
        )
        final_span.end()

    else:  # CHAT
        chat_dur   = random.uniform(0.4, 1.2)
        chat_start = t
        chat_span = trace.span(
            id         = id_helpers.generate_id(timestamp=chat_start),
            name       = "run_chat_workflow",
            type       = "llm",
            model      = MODEL,
            provider   = "openai",
            input      = {"messages": [
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user",   "content": question},
            ]},
            output     = {"choices": [{"message": {"content": answer}}]},
            usage      = make_usage(50, 150, 20, 80),
            start_time = chat_start,
            end_time   = chat_start + timedelta(seconds=chat_dur),
        )
        chat_span.end()

    # ── Close root trace ──────────────────────────────────────────────────────
    trace_end = trace_start + timedelta(seconds=total_dur)
    if trace_end.tzinfo is None:
        trace_end = trace_end.replace(tzinfo=timezone.utc)

    trace.end(end_time=trace_end, output={"assistant": answer})

    h_score = helpfulness_score(phase, is_misrouted=is_misrouted)
    trace.log_feedback_score(name="answer_helpfulness", value=h_score, reason="Synthetic user rating")
    trace.log_feedback_score(
        name   = "routing_correct",
        value  = 1.0 if routing_correct else 0.0,
        reason = "Correct route" if routing_correct else f"Misrouted to {route} (should be DATABASE)",
    )

    return h_score


# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────────
now          = datetime.now(timezone.utc)
total_traces = 0

for thread_idx in tqdm(range(NUM_THREADS), desc="Seeding OhmBot traces", unit="thread"):
    thread_id  = f"session-{uuid.uuid4().hex[:12]}"
    # Beta distribution skewed toward recent — more weight on last 10 days
    days_ago   = random.betavariate(2, 5) * DAYS_BACK
    phase      = 1 if days_ago > CUTOFF_DAYS else 2
    prompt_obj = _router_v1_obj if phase == 1 else _router_v2_obj

    thread_start = now - timedelta(days=days_ago, minutes=random.randint(0, 120))
    if thread_start.tzinfo is None:
        thread_start = thread_start.replace(tzinfo=timezone.utc)

    # In phase 1, V1_FAILURE_RATE of threads use a failure turn to simulate misrouting
    is_misrouted_thread = (phase == 1 and random.random() < V1_FAILURE_RATE)

    if is_misrouted_thread:
        turn_dict     = random.choice(V1_FAILURE_TURNS)
        route         = turn_dict["routed_as"]
        routing_correct = False
    else:
        route = random.choices(["DATABASE", "POLICY", "CHAT"], weights=ROUTE_WEIGHTS)[0]
        if route == "DATABASE":
            turn_dict = random.choice(DATABASE_TURNS)
        elif route == "POLICY":
            turn_dict = random.choice(POLICY_TURNS)
        else:
            turn_dict = random.choice(CHAT_TURNS)
        routing_correct = True

    follow_ups = list(turn_dict.get("follow_ups", []))
    random.shuffle(follow_ups)

    # Weights for [1, 2, 3, 4] turns → expected ~3 traces per thread
    num_turns   = random.choices([1, 2, 3, 4], weights=[5, 20, 50, 25])[0]
    turn_scores = []

    for turn in range(num_turns):
        turn_start = thread_start + timedelta(minutes=turn * random.uniform(2, 8))

        if turn == 0:
            question = turn_dict["question"]
            answer   = turn_dict["answer"]
            turn_route      = route
            turn_misrouted  = is_misrouted_thread
            turn_correct    = routing_correct
        elif follow_ups:
            question, answer = follow_ups.pop(0)
            # Follow-up turns use CHAT routing (they're short conversational replies)
            # and are considered correctly routed regardless of phase
            turn_route     = "CHAT"
            turn_misrouted = False
            turn_correct   = True
        else:
            question   = "Thanks, that's all I needed!"
            answer     = "Happy to help! Don't hesitate to reach out if anything comes up."
            turn_route     = "CHAT"
            turn_misrouted = False
            turn_correct   = True

        h = log_trace(
            thread_id       = thread_id,
            question        = question,
            answer          = answer,
            route           = turn_route,
            trace_start     = turn_start,
            phase           = phase,
            prompt_obj      = prompt_obj,
            routing_correct = turn_correct,
            is_misrouted    = turn_misrouted,
            sql             = turn_dict.get("sql"),
            context         = turn_dict.get("context"),
        )
        turn_scores.append(h)
        total_traces += 1

    # ── Thread-level feedback + flush ─────────────────────────────────────────
    client.flush()
    try:
        client.log_threads_feedback_scores(
            scores=[{
                "id":     thread_id,
                "name":   "user_frustration",
                "value":  frustration_score(turn_scores),
                "reason": f"{num_turns} turn(s), avg helpfulness {sum(turn_scores)/len(turn_scores):.2f}",
            }]
        )
    except Exception:
        pass  # Thread still active — will auto-close after inactivity

print(f"\n✅ Seeded {total_traces} traces across {NUM_THREADS} threads into '{PROJECT_NAME}'.")
print(f"   Phase 1 (V1, days {DAYS_BACK}–{CUTOFF_DAYS+1} ago): ~60% routing accuracy, lower helpfulness")
print(f"   Phase 2 (V2, days {CUTOFF_DAYS}–0 ago):  ~95% routing accuracy, higher helpfulness")
print(f"   Router Prompt versions registered in Opik Prompt Library ✓")

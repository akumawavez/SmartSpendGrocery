# ✅ **Problem Statement**

Grocery shopping is part of everyday life in the Netherlands, and for most people, Albert Heijn (AH) is the primary store. Yet AH receipts are difficult for shoppers to interpret or use for budgeting. Receipts contain *shorthand item names* (e.g., “BAP WIT”, “AH BIO MLK”), abbreviations, multi-line descriptions, discount indicators, and fragmented pricing information. These receipts are not consumer-friendly and make it nearly impossible to understand where money is actually going.

At the same time, AH has an enormous online catalogue with fully detailed, standardized product names and categories — groceries, bakery, household, produce, alcohol, personal care, etc. This catalogue also contains real-time prices and weekly promotions (bonus discounts, bonus box, 1+1 free, personal AH app discounts). None of this rich information is leveraged when a shopper looks at a simple receipt.

The problem is that **shoppers overspend without visibility into category-wise spending, missed discounts, or promotional optimization**, simply because receipts are unstructured, cryptic, and disconnected from the full catalogue.

SmartSpendGrocery-AH solves this by:

1. **Extracting items from raw AH receipts**, even shorthand ones.
2. **Matching them accurately to the correct items in the AH online catalogue** (via scraping + embedding similarity).
3. **Reconstructing real item names, categories, and prices** (verified against catalogue).
4. **Visualizing month-to-date, week-to-date, and category-wise spend in euros** using a Streamlit dashboard.
5. **Alerting users when they overshoot budgets.**

This is important because groceries are one of the largest recurring expenses for Dutch households, and improving visibility into spending directly improves financial control.

---

# ✅ **Why Agents?**

Albert Heijn receipts require **multi-step, context-aware reasoning**, and no single LLM call or rule-based script can reliably handle them. Agents are the right solution because:

### **1. AH receipts require multi-stage transformation**

* Extract item shorthand
* Cross-check product names
* Scrape AH online catalogue
* Compare prices
* Resolve ambiguous abbreviations (“BB ROERBAK”, “AH ECO TOM 500G”)
* Classify into categories
* Evaluate budgets

No single prompt or model call can perform all of these. An agent can.

---

### **2. Tool calling is unavoidable**

To process AH receipts correctly, the system must:

* **Scrape the AH web catalogue**
* **Search for product matches by title, brand, or price**
* **Extract promotions** (Bonus, 1+1 actions)
* **Store spend history in a local DB**

This is only feasible with agent tool orchestration.

---

### **3. Memory matters**

Shoppers’ spending patterns evolve over weeks and months. Budgets and category totals must persist beyond a single interaction. Agents allow:

* Short-term memory (current receipt context)
* Long-term memory (running totals and patterns)

---

### **4. Agents handle real-world ambiguity**

Shorthand item names often have:

* Missing vowels
* Truncated brand names
* Ambiguous categories

Agents using Gemini can interpret these cases with contextual reasoning.

---

### **5. Future promotional features require agent reasoning**

To evaluate promotions (e.g., “you missed a bonus discount available this week”), the system needs dynamic inference and comparisons — perfect for an LLM-powered agent.

For these reasons, an agentic architecture is the natural choice for this AH-specific grocery budgeting assistant.

---

# ✅ **What You Created — Architecture**

SmartSpendGrocery-AH is an agentic system built using Google ADK and Gemini, with a Streamlit GUI front-end.

### **Core Architecture**

```
Streamlit UI → SmartSpend Agent (ADK)
                    |
                    +-- Tool 1: AH Receipt Parser
                    |
                    +-- Tool 2: AH Catalogue Scraper
                    |
                    +-- Tool 3: Product Matcher (Embeddings + Price Matching)
                    |
                    +-- Tool 4: Category Classifier
                    |
                    +-- Tool 5: Spend Memory DB (SQLite)
                    |
                    +-- Tool 6: Budget Evaluator
                    |
                    +-- Tool 7: Dashboard Generator
```

---

### **Key Components**

#### **1. Streamlit Frontend**

* Upload AH receipt text or image
* Show extracted items
* Show matched product names and categories
* Display spend summaries, charts, and alerts

#### **2. AH Catalogue Scraper Tool**

Scrapes:

* Product title
* Category
* Current price
* Bonus promotions (if available)

#### **3. Receipt Parser Tool**

Uses Gemini to clean and parse shorthand item texts from receipts.

#### **4. Product Matcher Tool**

Uses:

* Embeddings from Gemini
* Price-based matching
  To resolve abbreviations and ambiguous matches.

#### **5. Spending Memory Tool**

Stores:

* Date
* Exact matched product
* Price paid
* Category
* Promotion applicability

#### **6. Budget Evaluator Tool**

Checks category-wise budgets (in euros):

* Daily
* Weekly
* Monthly

---

# ✅ **Demo — Showing the Solution**

This is what the user sees during the demo:

### **1. User uploads an AH receipt**

The receipt may contain shorthand lines like:

```
BAP WIT 6ST 1.79  
AH BIO MLK 1L 1.35  
BB ROERBAK ITAL 2.49  
```

### **2. Agent parses items**

The Bill Parser tool identifies probable product names.

### **3. Agent scrapes the AH website**

The Catalogue Scraper finds product info like:

* Product name
* Category (Bread, Dairy, Vegetables, etc)
* Price per unit
* Bonus promotions or 1+1 status

### **4. Agent matches receipt lines to catalogue items**

Using Gemini embeddings + price comparison.

### **5. Streamlit UI displays**

* A cleaned table of items
* The reconstructed real product names
* Category classifications
* Total spend in euros

### **6. Dashboard shows**

* Weekly spend chart
* Category-wise monthly distribution
* Budget gauge meters
* Alerts, e.g.:
  **“You exceeded your Weekly Snacks budget by €4.50.”**

### **7. (If promotion info is scraped)**

User sees notes like:
**“This item was available in Bonus this week; you could have saved €1.20.”**

---

# ✅ **The Build — How It Works**

SmartSpendGrocery-AH was built using:

### **1. Google ADK**

* Agent orchestrator
* Tool schemas
* Memory management
* Structured tool calling
* Tracing and observability

### **2. Google Gemini**

Used for:

* Receipt shorthand interpretation
* Item disambiguation
* Category classification
* Spending summaries
* Promotional reasoning

### **3. Streamlit**

GUI contains:

* File uploader
* Item tables
* Charts (Altair/Matplotlib)
* Alerts widget
* Budget dashboard

### **4. Python + SQLite**

* Persistent spend history
* Running monthly totals
* Category budgets

### **5. Web scraping tools**

Used to extract:

* AH product catalogue
* Pricing data
* Promotions

(Using requests/BeautifulSoup or built-in ADK-approved tools.)

### **6. Embedding-based similarity**

Used for:

* Matching shorthand item names to full catalogue entries
* Reducing ambiguity
* Handling misspellings or abbreviations

---

# ✅ **If I Had More Time, I Would Add…**

### **1. Full “Bonus Optimization Engine”**

* Highlight cheaper alternatives
* Recommend switching to bonus items
* Show potential weekly savings
* Calculate “what-if” savings for missed promotions

### **2. AH App Receipt QR Scanning**

Scan AH QR codes and fetch receipt data automatically.

### **3. Auto-detect promotions from weekly folder**

* Bonus folder
* Bonus box
* Personal AH app promotions

### **4. Meal Planning Integration**

Use matched items to suggest:

* Meal ideas
* Cost-saving recipes
* Shopping lists with cheapest combinations

### **5. Multi-receipt session summarization**

“Show me my spend across all AH trips in the last 30 days.”

### **6. Shared budgets for households**

Track combined expenses with partner/housemates.

---

# 🚀 **How to Use**

### **1. Environment Setup**
Ensure you have Python 3.10+ installed.

```bash
# Install uv if not already installed
pip install uv

# Create a virtual environment
uv venv adkapp

# Activate the virtual environment
# Windows:
.\adkapp\Scripts\activate
# Mac/Linux:
source adkapp/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### **2. Running the Application**
To start the agent system and the Streamlit UI:

```bash
streamlit run main.py
```

### **3. Interacting with the Agent**
1.  Upload a receipt image or text file.
2.  Wait for the agent to parse and categorize items.
3.  View the generated budget insights and alerts.



# Implementation Plan - SmartSpendGrocery (ADK Enhanced)

This plan outlines the architecture and implementation details for **SmartSpendGrocery**, leveraging advanced Google ADK concepts to create a robust, scalable, and agentic solution.

## Goal Description
To implement a production-ready, agentic grocery budgeting assistant that automates receipt processing, catalogue matching, and spending analysis using Google ADK. The system will transform raw receipts into actionable financial insights.

## User Review Required
> [!IMPORTANT]
> **Architecture Decision**: We are moving from a single-agent monolith to a **Multi-Agent System** to improve modularity and reliability.
> **Tooling**: We will use **MCP** for database interactions to standardize data access.
> **Deployment**: The system is designed to be deployable on **Google Cloud Run** for scalability.

## Proposed Architecture: Multi-Agent System

We will implement a **Hub-and-Spoke** architecture where a `Main Orchestrator Agent` coordinates specialized sub-agents.

### 1. Agents
*   **`OrchestratorAgent` (Router)**:
    *   **Role**: The entry point. Receives user input (receipt or query) and routes to the appropriate sub-agent.
    *   **Type**: **Agent powered by an LLM**.
    *   **Pattern**: **Sequential** (calls agents in order for receipt processing) or **Parallel** (if fetching data from multiple sources).
*   **`ReceiptProcessingAgent`**:
    *   **Role**: specialized in OCR and text parsing.
    *   **Type**: **Sequential Agent**.
    *   **Tools**: `ReceiptParser` (Custom).
*   **`CatalogueAgent`**:
    *   **Role**: Finds product details and promotions.
    *   **Type**: **Loop Agent** (iterates through items to find matches).
    *   **Tools**: `CatalogueScraper` (Custom), `Google Search` (Built-in).
*   **`FinanceAgent`**:
    *   **Role**: Manages budget, history, and alerts.
    *   **Type**: **Agent powered by an LLM**.
    *   **Tools**: `SpendingMemory` (MCP), `BudgetEvaluator` (Custom).
*   **`AnalystAgent`**:
    *   **Role**: Generates user-facing insights and summaries.
    *   **Type**: **Agent powered by an LLM**.
    *   **Context**: Uses **Context Compaction** to summarize large history.

### 2. Tools
We will utilize a mix of tool types:
*   **MCP (Model Context Protocol)**:
    *   `SQLiteMemoryServer`: Exposes the local SQLite database (spending history, budgets) via MCP. This allows standard read/write operations.
*   **Custom Tools**:
    *   `ReceiptParser`: Python tool wrapping OCR/LLM extraction logic.
    *   `CatalogueScraper`: Python tool using `BeautifulSoup`/`requests` to fetch AH product data.
    *   `ProductMatcher`: Embedding-based matching tool.
*   **Built-in Tools**:
    *   `Google Search`: Fallback for finding product details if scraping fails.
    *   `Code Execution`: For calculating complex budget projections or generating charts.
*   **OpenAPI**:
    *   (Optional) If we integrate with an external recipe API, we will use an OpenAPI tool definition.

### 3. Long-Running Operations & State
*   **Long-Running**: The `CatalogueAgent` might take time to scrape multiple items. We will implement **Pause/Resume** capabilities. If a product is ambiguous, the agent can pause and ask the user for clarification ("Did you mean 'Bio Milk' or 'Butter Milk'?").
*   **Sessions & Memory**:
    *   **`InMemorySessionService`**: Stores the current receipt processing state (extracted items, pending matches).
    *   **Long-Term Memory (Memory Bank)**: The SQLite DB serves as the persistent memory bank for user history.
    *   **Context Engineering**: We will implement a `HistorySummarizer` that compacts the last 30 days of spending into a concise context block for the `AnalystAgent`.

### 4. Observability & Evaluation
*   **Observability**:
    *   **Tracing**: All agent steps and tool calls will be traced using ADK's tracing integration (e.g., OpenTelemetry).
    *   **Metrics**: Track `MatchConfidenceScore` and `ProcessingTime`.
*   **Agent Evaluation**:
    *   **Golden Dataset**: A set of 50 diverse AH receipts with ground-truth parsed data.
    *   **Eval Pipeline**: An automated script that runs the `ReceiptProcessingAgent` against the golden set and calculates Precision/Recall for item extraction.

### 5. A2A Protocol & Deployment
*   **A2A**: The `OrchestratorAgent` communicates with sub-agents using a structured A2A protocol (passing JSON payloads with `task_id`, `context`, and `instructions`).
*   **Deployment**:
    *   Containerize the agent system using Docker.
    *   Deploy to **Google Cloud Run**.
    *   Frontend: Streamlit app connecting to the Agent API.

## Proposed Changes

### [New] Agent Definitions
#### [NEW] `agents/orchestrator.py`
#### [NEW] `agents/receipt_processor.py`
#### [NEW] `agents/catalogue_matcher.py`
#### [NEW] `agents/finance_manager.py`

### [New] Tools
#### [NEW] `tools/mcp_server.py` (SQLite MCP)
#### [NEW] `tools/scraper.py`
#### [NEW] `tools/parser.py`

### [New] Configuration
#### [NEW] `config/adk_config.yaml` (Tracing, Model settings)

## Verification Plan

### Automated Tests
*   **Unit Tests**: Test each tool independently (e.g., `test_scraper.py`, `test_parser.py`).
*   **Integration Tests**: Run a full flow with a sample receipt text and verify the DB is updated.
    ```bash
    python -m pytest tests/integration_test.py
    ```

### Manual Verification
1.  **Start the System**: Run `python main.py`.
2.  **Upload Receipt**: Use the Streamlit UI to upload `sample_receipt.jpg`.
3.  **Verify Extraction**: Check if items are correctly listed in the UI.
4.  **Verify Matching**: Check if "BAP" is matched to "Bananas".
5.  **Verify Budget**: Check if the "Snacks" budget alert triggers.
6.  **Check Traces**: Open the tracing dashboard to view the agent execution graph.

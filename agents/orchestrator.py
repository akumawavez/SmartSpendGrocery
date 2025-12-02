from agents.base import Agent
from agents.receipt_processor import ReceiptProcessingAgent
from agents.catalogue_matcher import CatalogueAgent
from agents.finance_manager import FinanceAgent
from agents.analyst import AnalystAgent


class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        self.receipt_agent = ReceiptProcessingAgent()
        self.catalogue_agent = CatalogueAgent()
        self.finance_agent = FinanceAgent()
        self.analyst_agent = AnalystAgent()
        self.finance_data = None  # Store finance data for UI access
        self.matched_items = None  # Store matched items for UI access

    def execute(self, receipt_file):
        # 1. Parse Receipt
        print("--- Step 1: Parsing Receipt ---")
        items = self.receipt_agent.run(receipt_file)

        # 2. Match with Catalogue
        print("--- Step 2: Matching Catalogue ---")
        matched_items = self.catalogue_agent.run(items)
        self.matched_items = matched_items  # Store for UI

        # 3. Update Finance & Check Budget
        print("--- Step 3: Finance Check ---")
        budget_status = self.finance_agent.run(matched_items)
        self.finance_data = budget_status  # Store for UI

        # 4. Generate Analysis
        print("--- Step 4: Analysis ---")
        summary = self.analyst_agent.run(budget_status)

        return summary

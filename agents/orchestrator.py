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

    def execute(self, receipt_file):
        # 1. Parse Receipt
        print("--- Step 1: Parsing Receipt ---")
        items = self.receipt_agent.run(receipt_file)
        
        # 2. Match with Catalogue
        print("--- Step 2: Matching Catalogue ---")
        matched_items = self.catalogue_agent.run(items)
        
        # 3. Update Finance & Check Budget
        print("--- Step 3: Finance Check ---")
        budget_status = self.finance_agent.run(matched_items)
        
        # 4. Generate Analysis
        print("--- Step 4: Analysis ---")
        summary = self.analyst_agent.run(budget_status)
        
        return summary

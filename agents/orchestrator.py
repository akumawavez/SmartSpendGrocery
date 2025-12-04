from agents.base import Agent
from agents.receipt_processor import ReceiptProcessingAgent
from agents.catalogue_matcher import CatalogueAgent
from agents.finance_manager import FinanceAgent
from agents.analyst import AnalystAgent
from config.llm_config import get_llm_config


class OrchestratorAgent(Agent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        
        # Initialize LLM configuration
        llm_config = get_llm_config()
        
        # Initialize agents with their respective models
        # Orchestrator uses gemini-1.5-pro
        orchestrator_model = llm_config.get_model('gemini-1.5-pro', 0.2)
        self.model = orchestrator_model
        
        # Receipt processor uses gemini-1.5-flash (faster for parsing)
        receipt_model = llm_config.get_model('gemini-1.5-flash', 0.1)
        self.receipt_agent = ReceiptProcessingAgent(model=receipt_model)
        
        # Catalogue matcher uses gemini-1.5-flash (faster for matching)
        catalogue_model = llm_config.get_model('gemini-1.5-flash', 0.1)
        self.catalogue_agent = CatalogueAgent(model=catalogue_model)
        
        # Finance agent uses gemini-1.5-pro (needs reasoning)
        finance_model = llm_config.get_model('gemini-1.5-pro', 0.2)
        self.finance_agent = FinanceAgent(model=finance_model)
        
        # Analyst agent uses gemini-1.5-pro (needs analysis)
        analyst_model = llm_config.get_model('gemini-1.5-pro', 0.3)
        self.analyst_agent = AnalystAgent(model=analyst_model)
        
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

from agents.base import Agent
from tools.mcp_server import SpendingMemoryMCP
from tools.budget_evaluator import BudgetEvaluator

class FinanceAgent(Agent):
    def __init__(self):
        super().__init__(name="FinanceManager")
        self.memory = SpendingMemoryMCP()
        self.evaluator = BudgetEvaluator()

    def execute(self, matched_items):
        print("Updating financial records...")
        
        # 1. Store transactions
        self.memory.add_transactions(matched_items)
        
        # 2. Calculate totals
        total_spend = sum(item['price'] for item in matched_items)
        category_breakdown = self.memory.get_category_totals()
        
        # 3. Check Budgets
        alerts = self.evaluator.check_budgets(category_breakdown)
        
        return {
            "total_spend": total_spend,
            "breakdown": category_breakdown,
            "alerts": alerts,
            "transactions": matched_items
        }

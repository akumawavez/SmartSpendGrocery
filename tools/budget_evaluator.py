class BudgetEvaluator:
    def __init__(self):
        # In a real app, this would fetch from the MCP server
        self.budgets = {
            "Fruit": 20.0,
            "Dairy": 15.0,
            "Vegetables": 25.0,
            "Alcohol": 30.0,
            "Snacks": 10.0
        }

    def check_budgets(self, current_totals):
        alerts = []
        print("Evaluating budgets...")
        for category, spent in current_totals.items():
            limit = self.budgets.get(category, 100.0)
            if spent > limit:
                alerts.append(f"WARNING: You have exceeded your {category} budget! (Spent: €{spent:.2f} / Limit: €{limit:.2f})")
            elif spent > limit * 0.8:
                alerts.append(f"CAUTION: You are nearing your {category} budget. (Spent: €{spent:.2f} / Limit: €{limit:.2f})")
        
        return alerts

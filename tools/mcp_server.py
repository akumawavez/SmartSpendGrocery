class SpendingMemoryMCP:
    def __init__(self):
        # Simulating a persistent store
        self.transactions = []
        self.budgets = {
            "Fruit": 20.0,
            "Dairy": 15.0,
            "Vegetables": 25.0,
            "Alcohol": 30.0,
            "Snacks": 10.0
        }

    def add_transactions(self, items):
        print(f"Stored {len(items)} transactions in Memory Bank.")
        self.transactions.extend(items)

    def get_category_totals(self):
        # Aggregate spend by category
        totals = {}
        for t in self.transactions:
            cat = t.get('category', 'Uncategorized')
            price = t.get('price', 0.0)
            totals[cat] = totals.get(cat, 0.0) + price
        return totals

    def get_budget_for_category(self, category):
        return self.budgets.get(category, 100.0) # Default budget

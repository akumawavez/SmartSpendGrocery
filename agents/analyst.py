from agents.base import Agent

class AnalystAgent(Agent):
    def __init__(self):
        super().__init__(name="Analyst")

    def execute(self, finance_data):
        print("Generating analysis...")
        
        total_spend = finance_data['total_spend']
        breakdown = finance_data['breakdown']
        alerts = finance_data['alerts']
        
        # In a real agent, this would be an LLM call with a prompt like:
        # "Analyze the following spending data and provide a helpful summary for the user."
        
        summary_lines = []
        summary_lines.append(f"**Total Spend:** €{total_spend:.2f}")
        summary_lines.append("**Category Breakdown:**")
        for cat, amount in breakdown.items():
            summary_lines.append(f"- {cat}: €{amount:.2f}")
            
        if alerts:
            summary_lines.append("\n**Alerts:**")
            for alert in alerts:
                summary_lines.append(f"- {alert}")
        else:
            summary_lines.append("\n**Status:** You are within your budget for all categories. Great job!")
            
        return "\n".join(summary_lines)

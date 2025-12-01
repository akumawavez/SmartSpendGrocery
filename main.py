import sys
import os

# Add the project root to the python path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import OrchestratorAgent

def main():
    print("Starting SmartSpendGrocery Agent System...")
    
    # Initialize the Orchestrator
    orchestrator = OrchestratorAgent()
    
    # Mock input file
    receipt_file = "sample_receipt.jpg"
    
    # Run the agent system
    result = orchestrator.run(receipt_file)
    
    print("\n" + "="*30)
    print("FINAL AGENT OUTPUT")
    print("="*30)
    print(result)
    print("="*30)

if __name__ == "__main__":
    main()

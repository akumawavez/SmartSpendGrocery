from agents.orchestrator import OrchestratorAgent
import sys
import os
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import tempfile

# Add the project root to the python path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Page configuration
st.set_page_config(
    page_title="SmartSpend Grocery",
    page_icon="🛒",
    layout="wide"
)

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = OrchestratorAgent()
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None
if 'finance_data' not in st.session_state:
    st.session_state.finance_data = None


def process_receipt(uploaded_file):
    """Process the uploaded receipt file through the agent system."""
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Run the orchestrator
        with st.spinner("Processing receipt through agent system (this may take a moment)..."):
            result = st.session_state.orchestrator.run(tmp_path)

            # Get finance data from orchestrator (stored during execution)
            finance_data = st.session_state.orchestrator.finance_data

            st.session_state.finance_data = finance_data
            st.session_state.processing_result = result

        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass  # Ignore cleanup errors

        return True
    except Exception as e:
        st.error(f"Error processing receipt: {str(e)}")
        st.exception(e)
        return False


# Main UI
st.title("🛒 SmartSpend Grocery - AH Receipt Analyzer")
st.markdown("Upload your Albert Heijn receipt to get insights into your spending, category breakdown, and budget alerts.")

# Sidebar for file upload
with st.sidebar:
    st.header("📄 Upload Receipt")
    uploaded_file = st.file_uploader(
        "Choose a receipt file",
        type=['jpg', 'jpeg', 'png', 'txt', 'pdf'],
        help="Upload an image or text file of your AH receipt"
    )

    if uploaded_file is not None:
        if st.button("Process Receipt", type="primary"):
            if process_receipt(uploaded_file):
                st.success("Receipt processed successfully!")
                st.rerun()

    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app uses AI agents to:")
    st.markdown("- Parse receipt items")
    st.markdown("- Match items to AH catalogue")
    st.markdown("- Track spending by category")
    st.markdown("- Alert on budget overruns")

# Main content area
if st.session_state.processing_result is None:
    st.info("👆 Please upload a receipt file using the sidebar to get started.")

    # Show example receipt format
    with st.expander("📋 Example Receipt Format"):
        st.code("""
BAP WIT 6ST 1.79
AH BIO MLK 1L 1.35
BB ROERBAK ITAL 2.49
AH TOMATEN 500G 1.99
        """)
else:
    # Display results
    finance_data = st.session_state.finance_data

    if finance_data:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Spend", f"€{finance_data['total_spend']:.2f}")

        with col2:
            num_items = len(finance_data.get('transactions', []))
            st.metric("Items", num_items)

        with col3:
            num_categories = len(finance_data.get('breakdown', {}))
            st.metric("Categories", num_categories)

        with col4:
            num_alerts = len(finance_data.get('alerts', []))
            alert_color = "🟢" if num_alerts == 0 else "🔴"
            st.metric("Alerts", f"{alert_color} {num_alerts}")

        st.markdown("---")

        # Transactions table
        if finance_data.get('transactions'):
            st.subheader("📋 Receipt Items")
            transactions_df = pd.DataFrame(finance_data['transactions'])

            # Select and rename columns for display
            display_cols = []
            col_mapping = {}

            if 'product_name' in transactions_df.columns:
                display_cols.append('product_name')
                col_mapping['product_name'] = 'Product Name'
            elif 'raw_name' in transactions_df.columns:
                display_cols.append('raw_name')
                col_mapping['raw_name'] = 'Product Name'

            if 'price' in transactions_df.columns:
                display_cols.append('price')
                col_mapping['price'] = 'Price (€)'

            if 'category' in transactions_df.columns:
                display_cols.append('category')
                col_mapping['category'] = 'Category'

            if 'is_bonus' in transactions_df.columns:
                display_cols.append('is_bonus')
                col_mapping['is_bonus'] = 'Bonus'

            if display_cols:
                display_df = transactions_df[display_cols].copy()
                display_df = display_df.rename(columns=col_mapping)
                # Format price column if it exists
                if 'Price (€)' in display_df.columns:
                    display_df['Price (€)'] = display_df['Price (€)'].apply(
                        lambda x: f"€{x:.2f}" if isinstance(x, (int, float)) else x)
                st.dataframe(display_df, use_container_width=True,
                             hide_index=True)
            else:
                st.dataframe(transactions_df,
                             use_container_width=True, hide_index=True)

        # Category breakdown
        if finance_data.get('breakdown'):
            st.subheader("📊 Category Breakdown")

            breakdown = finance_data['breakdown']
            breakdown_df = pd.DataFrame({
                'Category': list(breakdown.keys()),
                'Amount (€)': list(breakdown.values())
            }).sort_values('Amount (€)', ascending=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                # Bar chart
                chart = alt.Chart(breakdown_df).mark_bar().encode(
                    x=alt.X('Category', sort='-y'),
                    y=alt.Y('Amount (€)', title='Amount (€)'),
                    color=alt.Color('Category', legend=None)
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

            with col2:
                st.dataframe(
                    breakdown_df, use_container_width=True, hide_index=True)

        # Alerts
        if finance_data.get('alerts'):
            st.subheader("⚠️ Budget Alerts")
            for alert in finance_data['alerts']:
                st.warning(alert)
        else:
            st.success(
                "✅ You are within your budget for all categories. Great job!")

        # Analysis summary
        st.markdown("---")
        st.subheader("📝 Analysis Summary")
        st.markdown(st.session_state.processing_result)
    else:
        st.info("Processing completed. Waiting for data...")
        st.text(st.session_state.processing_result)

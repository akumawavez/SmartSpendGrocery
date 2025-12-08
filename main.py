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

# Initialize LLM configuration on startup
try:
    from config.llm_config import get_llm_config
    # This will load .env and configure Google LLM
    llm_config = get_llm_config()
    st.session_state.llm_configured = True
except Exception as e:
    st.session_state.llm_configured = False
    st.session_state.llm_error = str(e)


# Page configuration
st.set_page_config(
    page_title="SmartSpend Grocery",
    page_icon="🛒",
    layout="wide"
)

# Initialize session state
if 'orchestrator' not in st.session_state:
    # Check if LLM is configured before initializing orchestrator
    if not st.session_state.get('llm_configured', False):
        st.error(
            f"❌ LLM Configuration Error: {st.session_state.get('llm_error', 'Unknown error')}")
        st.info("""
        **Please set up your .env file:**
        1. Copy `.env.example` to `.env` (if it exists)
        2. Add your `GOOGLE_API_KEY` to the .env file
        3. Get your API key from: https://makersuite.google.com/app/apikey
        4. Restart the Streamlit app
        """)
        st.stop()
    st.session_state.orchestrator = OrchestratorAgent()
if 'processing_result' not in st.session_state:
    st.session_state.processing_result = None
if 'finance_data' not in st.session_state:
    st.session_state.finance_data = None
if 'budgets' not in st.session_state:
    # Initialize budgets from the finance agent
    if hasattr(st.session_state, 'orchestrator') and st.session_state.orchestrator:
        st.session_state.budgets = st.session_state.orchestrator.finance_agent.evaluator.budgets.copy()
    else:
        # Default budgets if orchestrator not ready
        st.session_state.budgets = {
            "Fruit": 20.0,
            "Dairy": 15.0,
            "Vegetables": 25.0,
            "Alcohol": 30.0,
            "Snacks": 10.0
        }
if 'monthly_totals' not in st.session_state:
    st.session_state.monthly_totals = {}


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

            # Update monthly totals from memory (cumulative)
            if finance_data:
                # Get cumulative totals from memory
                memory_totals = st.session_state.orchestrator.finance_agent.memory.get_category_totals()
                st.session_state.monthly_totals = memory_totals

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


def get_remaining_budget(category, spent, budget):
    """Calculate remaining budget for a category."""
    remaining = budget - spent
    percentage = (spent / budget * 100) if budget > 0 else 0
    return remaining, percentage


def update_budgets():
    """Update budgets in the finance agent and evaluator."""
    st.session_state.orchestrator.finance_agent.evaluator.budgets = st.session_state.budgets.copy()
    st.session_state.orchestrator.finance_agent.memory.budgets = st.session_state.budgets.copy()


# Main UI
st.title("🛒 SmartSpend Grocery - AH Receipt Analyzer")
st.markdown("Upload your Albert Heijn receipt to get insights into your spending, category breakdown, and budget alerts.")

# Create tabs
tab1, tab2 = st.tabs(["📄 Receipt Analyzer", "💰 Price Checker"])

# Sidebar for file upload and budget settings
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

    # Budget Settings Section
    st.header("💰 Budget Settings")
    st.markdown("Set monthly budget thresholds for each category:")

    # Get current monthly totals (prefer memory totals, fallback to finance_data)
    if hasattr(st.session_state, 'orchestrator') and st.session_state.orchestrator:
        current_totals = st.session_state.orchestrator.finance_agent.memory.get_category_totals()
    elif st.session_state.monthly_totals:
        current_totals = st.session_state.monthly_totals.copy()
    elif st.session_state.finance_data and st.session_state.finance_data.get('breakdown'):
        current_totals = st.session_state.finance_data.get('breakdown', {})
    else:
        current_totals = {}

    # Default categories if none exist
    default_categories = ["Fruit", "Dairy", "Vegetables",
                          "Alcohol", "Snacks", "Meat", "Bakery", "Beverages"]

    # Get all categories from budgets and current spending
    all_categories = set(list(st.session_state.budgets.keys()) +
                         list(current_totals.keys()) + default_categories)

    # Budget input fields
    budget_changed = False
    for category in sorted(all_categories):
        current_budget = st.session_state.budgets.get(category, 0.0)
        spent = current_totals.get(category, 0.0)

        col1, col2 = st.columns([2, 1])
        with col1:
            new_budget = st.number_input(
                f"{category}",
                min_value=0.0,
                value=float(current_budget),
                step=5.0,
                key=f"budget_{category}",
                help=f"Spent: €{spent:.2f}"
            )
        with col2:
            remaining, percentage = get_remaining_budget(
                category, spent, new_budget)
            if new_budget > 0:
                if remaining < 0:
                    st.markdown(
                        f"<span style='color:red'>€{abs(remaining):.0f} over</span>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<span style='color:green'>€{remaining:.0f} left</span>", unsafe_allow_html=True)

        if new_budget != current_budget:
            st.session_state.budgets[category] = new_budget
            budget_changed = True

    if budget_changed:
        update_budgets()
        st.rerun()

    # Add new category
    with st.expander("➕ Add New Category"):
        new_cat_name = st.text_input("Category Name", key="new_category_name")
        new_cat_budget = st.number_input(
            "Budget (€)", min_value=0.0, value=0.0, step=5.0, key="new_category_budget")
        if st.button("Add Category", key="add_category_btn"):
            if new_cat_name and new_cat_name.strip():
                st.session_state.budgets[new_cat_name.strip()] = float(
                    new_cat_budget)
                update_budgets()
                st.rerun()

    st.markdown("---")

    # Budget Remaining Summary
    st.header("📊 Budget Remaining (This Month)")
    if current_totals:
        for category in sorted(st.session_state.budgets.keys()):
            budget = st.session_state.budgets.get(category, 0.0)
            spent = current_totals.get(category, 0.0)
            remaining, percentage = get_remaining_budget(
                category, spent, budget)

            if budget > 0:
                st.markdown(f"**{category}**")
                # Progress bar
                progress_color = "green" if percentage < 80 else "orange" if percentage < 100 else "red"
                st.progress(min(percentage / 100, 1.0))
                st.caption(
                    f"€{spent:.2f} / €{budget:.2f} | Remaining: €{remaining:.2f}")
    else:
        st.info("No spending data yet. Upload a receipt to see budget tracking.")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("This app uses AI agents to:")
    st.markdown("- Parse receipt items")
    st.markdown("- Match items to AH catalogue")
    st.markdown("- Track spending by category")
    st.markdown("- Alert on budget overruns")

# Tab 1: Receipt Analyzer
with tab1:
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

            # Purchase Planning Section
            st.markdown("---")
            st.subheader("🛍️ Purchase Planning Assistant")

            # Get current spending and budgets (use cumulative totals from memory)
            if hasattr(st.session_state, 'orchestrator') and st.session_state.orchestrator:
                current_totals = st.session_state.orchestrator.finance_agent.memory.get_category_totals()
            else:
                current_totals = finance_data.get('breakdown', {})
            budgets = st.session_state.budgets

            # Calculate recommendations
            recommendations = []
            warnings = []

            for category in sorted(budgets.keys()):
                budget = budgets.get(category, 0.0)
                spent = current_totals.get(category, 0.0)
                remaining, percentage = get_remaining_budget(
                    category, spent, budget)

                if budget > 0:
                    if remaining < 0:
                        warnings.append({
                            'category': category,
                            'message': f"⚠️ {category}: You've exceeded your budget by €{abs(remaining):.2f}. Consider reducing purchases in this category.",
                            'remaining': remaining
                        })
                    elif remaining < budget * 0.2:  # Less than 20% remaining
                        recommendations.append({
                            'category': category,
                            'message': f"💡 {category}: Only €{remaining:.2f} remaining ({(remaining/budget*100):.1f}%). Plan carefully for remaining purchases.",
                            'remaining': remaining
                        })
                    elif percentage < 50:  # Less than 50% spent
                        recommendations.append({
                            'category': category,
                            'message': f"✅ {category}: You have €{remaining:.2f} remaining ({(remaining/budget*100):.1f}%). Good budget management!",
                            'remaining': remaining
                        })

            # Display warnings first
            if warnings:
                st.markdown("#### ⚠️ Budget Warnings")
                for warning in warnings:
                    st.warning(warning['message'])

            # Display recommendations
            if recommendations:
                st.markdown("#### 💡 Budget Recommendations")
                for rec in recommendations:
                    st.info(rec['message'])

            # Shopping suggestions based on budget
            st.markdown("#### 🛒 Shopping Suggestions")

            # Create a planning table
            planning_data = []
            for category in sorted(budgets.keys()):
                budget = budgets.get(category, 0.0)
                spent = current_totals.get(category, 0.0)
                remaining, percentage = get_remaining_budget(
                    category, spent, budget)

                if budget > 0:
                    status = "🟢 Safe" if percentage < 80 else "🟡 Caution" if percentage < 100 else "🔴 Over Budget"
                    suggestion = ""
                    if remaining > budget * 0.3:
                        suggestion = "You can shop freely in this category"
                    elif remaining > 0:
                        suggestion = f"Limit purchases to €{remaining:.2f} or less"
                    else:
                        suggestion = "Avoid additional purchases this month"

                    planning_data.append({
                        'Category': category,
                        'Budget': f"€{budget:.2f}",
                        'Spent': f"€{spent:.2f}",
                        'Remaining': f"€{remaining:.2f}",
                        'Status': status,
                        'Suggestion': suggestion
                    })

            if planning_data:
                planning_df = pd.DataFrame(planning_data)
                st.dataframe(
                    planning_df, use_container_width=True, hide_index=True)

                # Visual budget status chart
                st.markdown("#### 📈 Budget Status Overview")
                chart_data = []
                for item in planning_data:
                    spent_val = float(item['Spent'].replace('€', ''))
                    budget_val = float(item['Budget'].replace('€', ''))
                    percentage = (spent_val / budget_val *
                                  100) if budget_val > 0 else 0

                    # Determine color based on percentage
                    if percentage >= 100:
                        color = 'red'
                    elif percentage >= 80:
                        color = 'orange'
                    else:
                        color = 'green'

                    chart_data.append({
                        'Category': item['Category'],
                        'Percentage Used': percentage,
                        'Color': color
                    })

                status_df = pd.DataFrame(chart_data)

                chart = alt.Chart(status_df).mark_bar().encode(
                    x=alt.X('Category', sort='-y'),
                    y=alt.Y('Percentage Used', title='Budget Used (%)',
                            scale=alt.Scale(domain=[0, 120])),
                    color=alt.Color('Color', scale=alt.Scale(
                        domain=['green', 'orange', 'red'],
                        range=['#28a745', '#ffc107', '#dc3545']
                    ), legend=None)
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Set up budgets in the sidebar to get shopping suggestions.")
        else:
            st.info("Processing completed. Waiting for data...")
            st.text(st.session_state.processing_result)

# Tab 2: Price Checker
with tab2:
    st.header("💰 Price Checker")
    st.markdown(
        "Search for products on Albert Heijn and compare prices with and without AH membership.")

    # Initialize scraper in session state
    if 'price_checker_scraper' not in st.session_state:
        from tools.scraper import CatalogueScraper
        st.session_state.price_checker_scraper = CatalogueScraper()

    # Search input
    col_search, col_slider = st.columns([3, 1])
    with col_search:
        search_query = st.text_input(
            "🔍 Search for products",
            placeholder="Enter product name (e.g., 'bananas', 'milk', 'bread')",
            key="price_search_query"
        )
    with col_slider:
        max_results = st.slider(
            "Max results", min_value=10, max_value=50, value=20, key="max_results")

    if st.button("Search", type="primary", key="search_button") or search_query:
        if search_query:
            # Show translation info if applicable
            with st.spinner(f"Searching for '{search_query}' on Albert Heijn..."):
                # Translate query to Dutch (this will be done inside the scraper)
                # Search using Google Search via Gemini
                products = st.session_state.price_checker_scraper.search_products_google(
                    search_query,
                    max_results=max_results
                )

                if products:
                    st.success(f"Found {len(products)} product(s)")

                    # Group products by category
                    products_by_category = {}
                    for product in products:
                        category = product.get('category', 'Other')
                        if category == 'Unknown' or not category:
                            category = 'Other'
                        if category not in products_by_category:
                            products_by_category[category] = []
                        products_by_category[category].append(product)

                    # Create sub-tabs for each category
                    if len(products_by_category) > 1:
                        category_tabs = st.tabs(
                            list(products_by_category.keys()))
                    else:
                        # If only one category, still use tabs for consistency
                        category_tabs = st.tabs(
                            list(products_by_category.keys()))

                    # Display products in each category tab
                    for idx, (category, category_products) in enumerate(products_by_category.items()):
                        with category_tabs[idx]:
                            st.subheader(
                                f"📦 {category} ({len(category_products)} products)")

                            # Create a table-like display with products
                            # Header row
                            header_cols = st.columns([1.5, 3, 2, 2, 2, 2])
                            with header_cols[0]:
                                st.markdown("**Image**")
                            with header_cols[1]:
                                st.markdown("**Product**")
                            with header_cols[2]:
                                st.markdown("**Price (No Membership)**")
                            with header_cols[3]:
                                st.markdown("**Price (With Membership)**")
                            with header_cols[4]:
                                st.markdown("**Discount Offer**")
                            with header_cols[5]:
                                st.markdown("**Link**")

                            st.markdown("---")

                            # Display products in a table format
                            for product in category_products:
                                row_cols = st.columns([1.5, 3, 2, 2, 2, 2])

                                with row_cols[0]:
                                    # Display product image
                                    image_url = product.get('image_url', '')
                                    if image_url:
                                        try:
                                            st.image(image_url, width=80,
                                                     use_container_width=False)
                                        except:
                                            st.image(
                                                "https://via.placeholder.com/80?text=No+Image", width=80)
                                    else:
                                        st.image(
                                            "https://via.placeholder.com/80?text=No+Image", width=80)

                                with row_cols[1]:
                                    # Product name and details
                                    product_name = product.get(
                                        'name', 'Unknown Product')
                                    st.markdown(f"**{product_name}**")

                                    unit = product.get('unit', '')
                                    if unit:
                                        st.caption(f"📏 {unit}")

                                with row_cols[2]:
                                    # Price without membership - show full decimal precision
                                    price_without = product.get(
                                        'price_without_membership', 0)
                                    # Format to show full precision (up to 4 decimal places, remove trailing zeros)
                                    if price_without == int(price_without):
                                        price_str = f"{int(price_without)}.00"
                                    else:
                                        price_str = f"{price_without:.4f}".rstrip('0').rstrip('.')
                                        # Ensure at least 2 decimal places for currency
                                        if '.' not in price_str:
                                            price_str = f"{price_str}.00"
                                        elif len(price_str.split('.')[1]) == 1:
                                            price_str = f"{price_str}0"
                                    st.markdown(f"**€{price_str}**")

                                with row_cols[3]:
                                    # Price with membership - show full decimal precision
                                    price_with = product.get(
                                        'price_with_membership', price_without)
                                    savings = price_without - price_with if price_with < price_without else 0
                                    
                                    # Format to show full precision
                                    if price_with == int(price_with):
                                        price_with_str = f"{int(price_with)}.00"
                                    else:
                                        price_with_str = f"{price_with:.4f}".rstrip('0').rstrip('.')
                                        if '.' not in price_with_str:
                                            price_with_str = f"{price_with_str}.00"
                                        elif len(price_with_str.split('.')[1]) == 1:
                                            price_with_str = f"{price_with_str}0"

                                    if price_with < price_without:
                                        st.markdown(f"**€{price_with_str}**")
                                        # Format savings
                                        if savings == int(savings):
                                            savings_str = f"{int(savings)}.00"
                                        else:
                                            savings_str = f"{savings:.4f}".rstrip('0').rstrip('.')
                                            if '.' not in savings_str:
                                                savings_str = f"{savings_str}.00"
                                            elif len(savings_str.split('.')[1]) == 1:
                                                savings_str = f"{savings_str}0"
                                        st.caption(f"💵 Save: €{savings_str}")
                                    else:
                                        st.markdown(f"**€{price_with_str}**")

                                with row_cols[4]:
                                    # Discount offers
                                    discount_offer = product.get(
                                        'discount_offer', '')
                                    is_bonus = product.get('is_bonus', False)
                                    if discount_offer:
                                        st.markdown(f"🎁 **{discount_offer}**")
                                    elif is_bonus:
                                        st.markdown("🎁 **BONUS**")
                                    else:
                                        st.markdown("—")

                                with row_cols[5]:
                                    # Product link
                                    product_url = product.get('url', '')
                                    if product_url:
                                        st.markdown(f"[🔗 View]({product_url})")
                                    else:
                                        st.markdown("—")

                                st.markdown("---")

                            # Summary for this category
                            if len(category_products) > 0:
                                st.markdown("#### 📊 Category Summary")
                                cat_col1, cat_col2, cat_col3 = st.columns(3)

                                with cat_col1:
                                    avg_no_member = sum([p.get(
                                        'price_without_membership', 0) for p in category_products]) / len(category_products)
                                    st.metric("Avg (No Membership)",
                                              f"€{avg_no_member:.2f}")

                                with cat_col2:
                                    avg_member = sum([p.get('price_with_membership', p.get(
                                        'price_without_membership', 0)) for p in category_products]) / len(category_products)
                                    st.metric("Avg (With Membership)",
                                              f"€{avg_member:.2f}")

                                with cat_col3:
                                    total_savings_cat = sum([max(0, p.get('price_without_membership', 0) - p.get(
                                        'price_with_membership', p.get('price_without_membership', 0))) for p in category_products])
                                    st.metric("Total Savings",
                                              f"€{total_savings_cat:.2f}")

                    # Overall summary
                    if len(products_by_category) > 1:
                        st.markdown("---")
                        st.subheader("📊 Overall Summary")

                        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(
                            4)

                        with summary_col1:
                            total_products = len(products)
                            st.metric("Total Products", total_products)

                        with summary_col2:
                            avg_price_no_member = sum(
                                [p.get('price_without_membership', 0) for p in products]) / len(products)
                            st.metric("Avg Price (No Membership)",
                                      f"€{avg_price_no_member:.2f}")

                        with summary_col3:
                            avg_price_member = sum([p.get('price_with_membership', p.get(
                                'price_without_membership', 0)) for p in products]) / len(products)
                            st.metric("Avg Price (With Membership)",
                                      f"€{avg_price_member:.2f}")

                        with summary_col4:
                            total_savings = sum([max(0, p.get('price_without_membership', 0) - p.get(
                                'price_with_membership', p.get('price_without_membership', 0))) for p in products])
                            st.metric("Total Potential Savings",
                                      f"€{total_savings:.2f}")
                else:
                    st.warning(
                        "No products found. Try a different search query or check your internet connection.")
                    st.info(
                        "💡 Tip: Try searching for common products like 'bananas', 'milk', 'bread', or 'chicken'")
        else:
            st.info(
                "👆 Enter a product name above to search for prices on Albert Heijn.")

    # Instructions
    with st.expander("ℹ️ How to use Price Checker"):
        st.markdown("""
        **Price Checker Features:**
        - Search for any product by full or partial name
        - View prices with and without AH Premium membership
        - See potential savings with membership
        - Compare prices across multiple products
        - Identify bonus/promotional items
        
        **How it works:**
        1. Enter a product name in the search box (e.g., "bananas", "organic milk")
        2. Click "Search" or press Enter
        3. View results showing prices for both membership types
        4. Compare prices and see potential savings
        
        **Note:** This feature uses Google Search and AI to find products on Albert Heijn's website.
        Prices are extracted from search results and may vary from actual store prices.
        """)

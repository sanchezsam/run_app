import os
import re

def apply_app_tabs_patch():
    target_file = "app.py"
    if not os.path.exists(target_file):
        print(f"❌ Error: {target_file} not found.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Define replacement strings for tabs based on the issue [INDEX]
    new_tabs_segment = """# ==========================================
# MASTER TAB CONTROLLERS (STATE PERSISTENT)
# ==========================================

if "active_tab_selection" not in st.session_state:
    st.session_state.active_tab_selection = "Calendar"

tab_titles = [
    '🏠 Dashboard Overview', 'Telemetry Sync', 'Biometric Coliseum',
    'Pro Shop & Garage', 'Performance Analytics', 'Training Ledger', 'Calendar'
]

# Render interactive radio layout inside a container
st.session_state.active_tab_selection = st.radio(
    label="Navigate Viewports:",
    options=tab_titles,
    index=tab_titles.index(st.session_state.active_tab_selection) if st.session_state.active_tab_selection in tab_titles else 6,
    horizontal=True,
    label_visibility="collapsed"
)

# Convert stateless 'with' blocks into state-persistent conditional routing
if st.session_state.active_tab_selection == '🏠 Dashboard Overview':"""

    # Apply structural changes via regex to handle whitespace variations [INDEX]
    pattern = r"tab_titles\s*=\s*\[.*?\]\s*tab0,\s*tab1,.*?=\s*st\.\s*tabs\(.*?\)\s*with\s*tab0\s*:"
    content = re.sub(pattern, new_tabs_segment, content, flags=re.DOTALL)

    # Convert remaining 'with tabX:' blocks to state checks
    replacements = {
        "with tab1:": "if st.session_state.active_tab_selection == 'Telemetry Sync':",
        "with tab2:": "if st.session_state.active_tab_selection == 'Biometric Coliseum':",
        "with tab3:": "if st.session_state.active_tab_selection == 'Pro Shop & Garage':",
        "with tab4:": "if st.session_state.active_tab_selection == 'Performance Analytics':",
        "with tab5:": "if st.session_state.active_tab_selection == 'Training Ledger':",
        "with tab6:": "if st.session_state.active_tab_selection == 'Calendar':"
    }
    for old, new in replacements.items():
        content = content.replace(old, new)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("🎉 app.py successfully refactored!")

if __name__ == "__main__":
    apply_app_tabs_patch()


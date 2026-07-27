# patch_coliseum.py (Indentation & Anchor-Free Dynamic Scanner)
import os

def apply_bulletproof_patch():
    target_file = "coliseum_ui.py"
    
    if not os.path.exists(target_file):
        print(f"Error: Could not locate '{target_file}' in your workspace folder.")
        return

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Step 1: Scan for the exact execution index row inside the button logic
        target_idx = -1
        for idx, line in enumerate(lines):
            if "format_finish_time(p_total_seconds)" in line.replace(" ", ""):
                # Find the very next line containing r_time_str to anchor the injection point
                for sub_idx in range(idx, min(idx + 10, len(lines))):
                    if "r_time_str" in lines[sub_idx]:
                        target_idx = sub_idx
                        break
                if target_idx != -1:
                    break

        if target_idx == -1:
            # Fallback scan: Search for the unique math scoring engine assignment variable
            for idx, line in enumerate(lines):
                if "calc_racing_score" in line:
                    target_idx = idx - 1
                    break

        if target_idx != -1:
            # Step 2: Auto-detect parent indentation context spaces to prevent alignment syntax errors
            target_line = lines[target_idx]
            indent_spaces = ""
            for char in target_line:
                if char.isspace():
                    indent_spaces += char
                else:
                    break
            if not indent_spaces:
                indent_spaces = "    "

            # Step 3: Format the payload array matching your custom style perfectly
            progress_payload = [
                f"\n",
                f"{indent_spaces}# =========================================================================\n",
                f"{indent_spaces}# INJECTED: LIVE PROGRESS BARS WITH MILE SELECTION AND 5-SECOND FINISH FREEZE\n",
                f"{indent_spaces}# =========================================================================\n",
                f"{indent_spaces}distance_placeholder = st.empty()\n",
                f"{indent_spaces}commentary_placeholder = st.empty()\n",
                f"{indent_spaces}player_bar_placeholder = st.empty()\n",
                f"{indent_spaces}rival_bar_placeholder = st.empty()\n",
                f"{indent_spaces}total_dist = course_specs['dist']\n\n",
                
                f"{indent_spaces}# STAGE 1: THE START LINE\n",
                f"{indent_spaces}distance_placeholder.markdown('### 📍 **Mile 0.00** / ' + str(round(total_dist, 2)) + ' Mi')\n",
                f"{indent_spaces}commentary_placeholder.info('🟢 **START LINE:** The starter pistol fires! You and **' + str(selected_boss) + '** surge out of the blocks across the **' + str(parsed_course_key) + '**!')\n",
                f"{indent_spaces}player_bar_placeholder.progress(0.15, text='🏃‍♂️ **Your Progress** (15%)')\n",
                f"{indent_spaces}rival_bar_placeholder.progress(0.15, text='⚡ **' + str(selected_boss) + '** (15%)')\n",
                f"{indent_spaces}time.sleep(3.0)\n\n",
                
                f"{indent_spaces}# STAGE 2: THE MID-RACE ACCELERATION\n",
                f"{indent_spaces}mid_mile = round(total_dist * 0.5, 2)\n",
                f"{indent_spaces}distance_placeholder.markdown('### 📍 **Mile ' + str(mid_mile) + '** / ' + str(round(total_dist, 2)) + ' Mi')\n",
                f"{indent_spaces}if total_3wk_miles >= 30.0:\n",
                f"{indent_spaces}    commentary_placeholder.success('⚡ **MID-RACE BREAKDOWN:** Your strong 3-week fitness load of **' + str(round(total_3wk_miles, 1)) + ' miles** is providing a solid aerobic stamina buffer. You match **' + str(selected_boss) + '** stride-for-stride!')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(0.55, text='🏃‍♂️ **Your Progress** (55%)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(0.50, text='⚡ **' + str(selected_boss) + '** (50%)')\n",
                f"{indent_spaces}else:\n",
                f"{indent_spaces}    commentary_placeholder.warning('🥵 **MID-RACE BREAKDOWN:** Aerobic pressure mounting! Your limited 3-week volume of **' + str(round(total_3wk_miles, 1)) + ' miles** leaves you searching for deep recovery reserves. Pacer takes the lead!')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(0.42, text='🏃‍♂️ **Your Progress** (42%)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(0.55, text='⚡ **' + str(selected_boss) + '** (55%)')\n",
                f"{indent_spaces}time.sleep(3.5)\n\n",
                
                f"{indent_spaces}# STAGE 3: THE HOME STRETCH\n",
                f"{indent_spaces}stretch_mile = round(total_dist * 0.9, 2)\n",
                f"{indent_spaces}distance_placeholder.markdown('### 📍 **Mile ' + str(stretch_mile) + '** / ' + str(round(total_dist, 2)) + ' Mi')\n",
                f"{indent_spaces}if total_kit_physics_bonus >= 0.50:\n",
                f"{indent_spaces}    commentary_placeholder.success('👟 **THE HOME STRETCH:** Your equipped gear advantage of **+' + str(round(total_kit_physics_bonus, 2)) + ' points** activates! Carbon-plated shoes grant maximum closing velocity!')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(0.92, text='🏃‍♂️ **Your Progress** (92%)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(0.85, text='⚡ **' + str(selected_boss) + '** (85%)')\n",
                f"{indent_spaces}else:\n",
                f"{indent_spaces}    commentary_placeholder.info('🏁 **THE HOME STRETCH:** Minimal kit enhancements detected. It\\'s a dead heat, high-cadence sprint to the tape!')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(0.85, text='🏃‍♂️ **Your Progress** (85%)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(0.86, text='⚡ **' + str(selected_boss) + '** (86%)')\n",
                f"{indent_spaces}time.sleep(2.5)\n\n",
                
                f"{indent_spaces}# STAGE 4: THE FINISH LINE WITH A 5-SECOND STATE HOLD\n",
                f"{indent_spaces}distance_placeholder.markdown('### 🏁 **Mile ' + str(round(total_dist, 2)) + ' (Finished)** / ' + str(round(total_dist, 2)) + ' Mi')\n",
                f"{indent_spaces}if p_total_seconds < r_total_seconds:\n",
                f"{indent_spaces}    commentary_placeholder.success('🏁 **FINISH LINE REACHED:** Absolute triumph! You cross the finish line tape fractions of a second ahead of **' + str(selected_boss) + '**!')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(1.00, text='🏃‍♂️ **Your Progress** (100% - Finished)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(0.98, text='⚡ **' + str(selected_boss) + '** (98% - Finished)')\n",
                f"{indent_spaces}else:\n",
                f"{indent_spaces}    commentary_placeholder.error('🏁 **FINISH LINE REACHED:** Heartbreak at the line! **' + str(selected_boss) + '** out-leans you at the tape to claim victory.')\n",
                f"{indent_spaces}    player_bar_placeholder.progress(0.98, text='🏃‍♂️ **Your Progress** (98% - Finished)')\n",
                f"{indent_spaces}    rival_bar_placeholder.progress(1.00, text='⚡ **' + str(selected_boss) + '** (100% - Finished)')\n",
                f"{indent_spaces}time.sleep(5.0)\n\n",
                
                f"{indent_spaces}# Dismount animation canvases to smoothly reveal summary boxes\n",
                f"{indent_spaces}distance_placeholder.empty()\n",
                f"{indent_spaces}commentary_placeholder.empty()\n",
                f"{indent_spaces}player_bar_placeholder.empty()\n",
                f"{indent_spaces}rival_bar_placeholder.empty()\n",
                f"{indent_spaces}# =========================================================================\n\n"
            ]

            # Inject the full loop payload below the tracked index position
            lines[target_idx + 1:target_idx + 1] = progress_payload
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print("✨ Success! 'coliseum_ui.py' has been patched cleanly with the dynamic race loops.")
        else:
            print("Error: Could not locate variable definitions inside your local file layout.")

    except Exception as patch_err:
        print(f"An unexpected loop execution parsing error occurred: {patch_err}")

if __name__ == "__main__":
    apply_bulletproof_patch()


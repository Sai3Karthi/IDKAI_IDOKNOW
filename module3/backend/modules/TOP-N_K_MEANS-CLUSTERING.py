import json
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

# --- DATA LOADING AND VISUALIZATION FUNCTIONS (No changes here) ---

def load_perspectives_from_file(filename: str):
    """Loads the perspectives from a single, complete JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("input"), data.get("perspectives")
    except FileNotFoundError:
        print(f"!!! ERROR: The file was not found at the expected path: {os.path.abspath(filename)}")
        sys.exit(1)
    return None, None

# --- NEW CORE LOGIC FUNCTIONS ---

def determine_target_size(num_perspectives: int) -> int:
    """
    Determines the target number of perspectives to keep (k) based on the input size.
    """
    if 7 <= num_perspectives <= 14:
        k = 6
    elif 15 <= num_perspectives <= 28:
        k = 14
    elif 29 <= num_perspectives <= 77:
        k = 21
    elif 78 <= num_perspectives <= 136:
        k = 28
    else:
        # Default or for sizes outside the defined ranges
        k = num_perspectives 
    
    # Ensure we don't try to select more than we have
    return min(k, num_perspectives)

def stratified_selection_and_distribution(perspectives: list):
    """
    Performs the entire reduction and distribution process:
    1. Determines the target size 'k' based on the total number of perspectives.
    2. Categorizes all perspectives by bias.
    3. Calculates a proportional number of slots for each category.
    4. Selects the most significant perspectives from each category to fill the slots.
    """
    leftist_pool, rightist_pool, common_pool = [], [], []
    LEFTIST_THRESHOLD, RIGHTIST_THRESHOLD = 0.428, 0.571

    # 1. Categorize all perspectives
    for p in perspectives:
        bias = p.get('bias_x', 0.5)
        if bias < LEFTIST_THRESHOLD: leftist_pool.append(p)
        elif bias > RIGHTIST_THRESHOLD: rightist_pool.append(p)
        else: common_pool.append(p)
    
    total_perspectives = len(perspectives)
    print(f"Initial distribution: {len(leftist_pool)} Leftist, {len(common_pool)} Common, {len(rightist_pool)} Rightist.")

    # 2. Determine the total number of perspectives to keep
    target_k = determine_target_size(total_perspectives)
    print(f"Based on {total_perspectives} inputs, the target size is {target_k}.")

    if target_k == total_perspectives:
        print("Number of perspectives is within the target range. No reduction needed.")
        return leftist_pool, rightist_pool, common_pool

    # 3. Calculate proportional slots for each category
    left_proportion = len(leftist_pool) / total_perspectives if total_perspectives > 0 else 0
    right_proportion = len(rightist_pool) / total_perspectives if total_perspectives > 0 else 0
    common_proportion = len(common_pool) / total_perspectives if total_perspectives > 0 else 0

    num_leftist = round(left_proportion * target_k)
    num_rightist = round(right_proportion * target_k)
    num_common = round(common_proportion * target_k)
    
    # Adjust for rounding errors to ensure the total is exactly target_k
    while (num_leftist + num_rightist + num_common) != target_k:
        if (num_leftist + num_rightist + num_common) > target_k:
            # If we have too many, remove one from the largest group
            if num_leftist > num_rightist and num_leftist > num_common: num_leftist -= 1
            elif num_rightist > num_common: num_rightist -= 1
            else: num_common -= 1
        else:
            # If we have too few, add one to the smallest group
            if num_leftist < num_rightist and num_leftist < num_common: num_leftist += 1
            elif num_rightist < num_common: num_rightist += 1
            else: num_common += 1
    
    print(f"Calculated fair distribution: {num_leftist} Leftist, {num_common} Common, {num_rightist} Rightist.")

    # 4. Sort each pool by significance and select the top N
    leftist_pool.sort(key=lambda p: p['significance_y'], reverse=True)
    rightist_pool.sort(key=lambda p: p['significance_y'], reverse=True)
    common_pool.sort(key=lambda p: p['significance_y'], reverse=True)
    
    final_leftist = leftist_pool[:int(num_leftist)]
    final_rightist = rightist_pool[:int(num_rightist)]
    final_common = common_pool[:int(num_common)]
    
    return final_leftist, final_rightist, final_common

# --- SAVE AND VISUALIZATION FUNCTIONS (No logic changes) ---
def save_agents_data(leftist_data, rightist_data, common_data, output_dir="."):
    """Saves the distributed perspectives to separate JSON files."""
    # The output files will be created inside the same directory as the script (modules/)
    with open(os.path.join(output_dir, 'leftist.json'), 'w', encoding='utf-8') as f:
        json.dump(leftist_data, f, indent=4)

    with open(os.path.join(output_dir, 'rightist.json'), 'w', encoding='utf-8') as f:
        json.dump(rightist_data, f, indent=4)

    with open(os.path.join(output_dir, 'common.json'), 'w', encoding='utf-8') as f:
        json.dump(common_data, f, indent=4)

def create_visualization(leftist_data, rightist_data, common_data, original_topic, output_dir="."):
    """Creates and saves a scatter plot visualizing the perspective distribution."""
    LEFTIST_THRESHOLD, RIGHTIST_THRESHOLD = 3*0.143, 4*0.143
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 9))

    # Draw background zones for the political spectrum
    ax.axvspan(0, LEFTIST_THRESHOLD, facecolor='red', alpha=0.1, label='Leftist Zone')
    ax.axvspan(LEFTIST_THRESHOLD, RIGHTIST_THRESHOLD, facecolor='green', alpha=0.1, label='Common Zone')
    ax.axvspan(RIGHTIST_THRESHOLD, 1.0, facecolor='purple', alpha=0.1, label='Rightist Zone')

    # Plot the perspective points for each group
    if leftist_data:
        ax.scatter([p['bias_x'] for p in leftist_data], [p['significance_y'] for p in leftist_data],
                   color='#E63946', s=120, edgecolor='black', label='Leftist Perspectives', zorder=5)
    if common_data:
        ax.scatter([p['bias_x'] for p in common_data], [p['significance_y'] for p in common_data],
                   color='#588157', s=120, edgecolor='black', label='Common Perspectives', zorder=5)
    if rightist_data:
        ax.scatter([p['bias_x'] for p in rightist_data], [p['significance_y'] for p in rightist_data],
                   color='#6A057F', s=120, edgecolor='black', label='Rightist Perspectives', zorder=5)

    # Formatting the plot for clarity and aesthetics
    ax.set_title(f'Political Spectrum Visualization for:\n"{original_topic}"', fontsize=16, pad=20)
    ax.set_xlabel('Bias (Left < 0.36 | Center | Right > 0.64)', fontsize=12, labelpad=15)
    ax.set_ylabel('Significance', fontsize=12, labelpad=15)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1.1))
    fig.tight_layout()
    
    # Save the plot to a file
    output_path = os.path.join(output_dir, 'debate_visualization.png')
    plt.savefig(output_path) # Updated thresholds
    # ... (rest of the plotting code is unchanged, but will use the new thresholds)

# Main execution block
if __name__ == "__main__":
    # --- CONFIGURATION ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    DATA_FILENAME = os.path.join(script_dir, "../output.json")
    output_directory = os.path.join(script_dir, "../final_output")
    os.makedirs(output_directory, exist_ok=True)
    
    # --- 1. LOAD DATA ---
    print(f"Attempting to load perspectives from: {os.path.abspath(DATA_FILENAME)}")
    original_info, all_perspectives = load_perspectives_from_file(DATA_FILENAME)
    
    if not all_perspectives: sys.exit()

    print(f"\nOriginal Topic: \"{original_info}\""); print(f"Loaded {len(all_perspectives)} perspectives.")
    
    # --- 2. PERFORM STRATIFIED SELECTION AND DISTRIBUTION ---
    print("\nStarting adaptive selection and distribution process...")
    leftist_args, rightist_args, shared_args = stratified_selection_and_distribution(all_perspectives)

    # --- 3. DISPLAY RESULTS ---
    print("\n" + "="*50)
    print("          DEBATE SETUP COMPLETE")
    print("="*50)
    # ... (display code is unchanged)

    # --- 4. SAVE AND VISUALIZE ---
    save_agents_data(leftist_args, rightist_args, shared_args, output_dir=output_directory)
    create_visualization(leftist_args, rightist_args, shared_args, original_info, output_dir=output_directory)
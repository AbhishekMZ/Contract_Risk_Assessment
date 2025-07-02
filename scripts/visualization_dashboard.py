# visualization_dashboard.py
import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import sys # Add this import

DETECTION_DIR = "Detection_Results"
REPORTS_DIR = "Reports" 
MANIFEST_FILE = os.path.join(DETECTION_DIR, "detection_manifest.json")
PLOT_FILE = os.path.join(REPORTS_DIR, "vulnerability_distribution.png")

def create_visualizations():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: Detection manifest '{os.path.abspath(MANIFEST_FILE)}' not found. Run loophole detection first.")
        sys.exit(1) # Exit with error code

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    # ... rest of the create_visualizations function ...
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    all_findings_list = []

    print("Generating visualizations...")

    for contract_key, report_path in manifest.items():
        if not os.path.exists(report_path):
            print(f"Warning: Report file not found at {report_path} for {contract_key}")
            continue
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f_report:
                data = json.load(f_report)
            
            for finding in data.get("slither_findings", []):
                all_findings_list.append({
                    "contract": contract_key,
                    "source": "Slither",
                    "check": finding.get("check", "Unknown"),
                    "impact": finding.get("impact", "N/A")
                })
            for finding in data.get("custom_findings", []):
                 all_findings_list.append({
                    "contract": contract_key,
                    "source": "Custom",
                    "check": finding.get("check", "Unknown"),
                    "impact": finding.get("impact", "N/A") 
                })
        except Exception as e:
            print(f"Error processing report file {report_path}: {e}")

    if not all_findings_list:
        print("No findings to visualize.")
        # Create empty plot files or skip if preferred
        # For now, just return
        print("\n--- Visualization Summary ---")
        print("No findings were available to generate plots.")
        return

    df = pd.DataFrame(all_findings_list)

    if not df.empty and 'check' in df.columns:
        plt.figure(figsize=(12, max(8, len(df['check'].unique()) * 0.4))) # Adjust height dynamically
        df['full_check_name'] = df['source'] + ": " + df['check']
        sns.countplot(y='full_check_name', data=df, order = df['full_check_name'].value_counts().index, palette="viridis")
        plt.title('Distribution of Detected Vulnerability Types')
        plt.xlabel('Count')
        plt.ylabel('Vulnerability Type (Source: Check Name)')
        plt.tight_layout()
        plt.savefig(PLOT_FILE)
        print(f"Vulnerability distribution plot saved to '{PLOT_FILE}'")
        plt.close()
    else:
        print("No 'check' data to plot for vulnerability distribution.")

    if not df.empty and 'impact' in df.columns:
        # Standardize impact values (e.g., map 'High', 'Medium', 'Low', 'Informational', 'Optimization')
        impact_order = ['High', 'Medium', 'Low', 'Informational', 'Optimization', 'N/A'] # Define desired order
        df['impact_standardized'] = pd.Categorical(df['impact'], categories=impact_order, ordered=True)

        plt.figure(figsize=(10, 6))
        sns.countplot(x='impact_standardized', data=df, hue='source', palette="magma", order=impact_order)
        plt.title('Vulnerabilities by Impact Level')
        plt.xlabel('Impact Level')
        plt.ylabel('Count')
        plt.tight_layout()
        impact_plot_file = os.path.join(REPORTS_DIR, "vulnerability_impact_distribution.png")
        plt.savefig(impact_plot_file)
        print(f"Vulnerability impact plot saved to '{impact_plot_file}'")
        plt.close()
    else:
        print("No 'impact' data to plot for impact distribution.")
        
    print("\n--- Visualization Summary ---")
    if not df.empty:
        print(f"Generated plots based on {len(df)} total findings.")
    else:
        print("No findings were available to generate plots.") # Already handled above


if __name__ == "__main__":
    create_visualizations()
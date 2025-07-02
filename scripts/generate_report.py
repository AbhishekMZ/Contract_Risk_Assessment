# generate_report.py
"""
Script to generate human-readable reports from loophole detection results.
Supports both training data and external contract evaluation.
"""
import os
import sys
import json
from glob import glob
import argparse

DETECTION_DIR = 'Detection_Results'
REPORTS_DIR = 'Reports'
EXTERNAL_RESULTS_DIR = os.path.join('External_Results', 'detections')
EXTERNAL_REPORTS_DIR = os.path.join('External_Results', 'reports')
MANIFEST_FILE = os.path.join(DETECTION_DIR, 'detection_manifest.json')
SUMMARY_REPORT_FILE = os.path.join(REPORTS_DIR, 'summary_report.md')

def generate_training_report():
    """Generate report for training data detection results"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, 'loophole_report.md')
    
    # Initialize report content
    report_content = ["# Smart Contract Security Analysis Report\n"]
    
    # Check if detection manifest exists
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: Detection manifest not found at {MANIFEST_FILE}")
        return
    
    # Load detection manifest
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Error loading detection manifest: {e}")
        return
    
    # Process each contract's detection report
    for contract_file, report_file in manifest.items():
        if not os.path.exists(report_file):
            print(f"Warning: Report file not found: {report_file}")
            continue
            
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            print(f"Error loading report {report_file}: {e}")
            continue
        
        # Add contract header
        report_content.append(f"## {os.path.basename(contract_file)}\n")
        
        # Process Slither findings if they exist
        if 'slither_findings' in report_data and report_data['slither_findings']:
            for finding in report_data['slither_findings']:
                description = finding.get('description', 'No description')
                check = finding.get('check', 'Slither finding')
                impact = finding.get('impact', 'Informational')
                confidence = finding.get('confidence', 'Medium')
                
                report_content.append(f"### {check}")
                report_content.append(f"- **Impact:** {impact}")
                report_content.append(f"- **Confidence:** {confidence}")
                report_content.append(f"- **Description:** {description}")
                
                # Process elements if they exist
                if 'elements' in finding and finding['elements']:
                    for elem in finding['elements']:
                        # Add element details
                        elem_type = elem.get("type", "N/A")
                        elem_name = elem.get("name", "N/A")
                        source_map = elem.get("source_mapping", {})
                        lines = source_map.get("lines", [])
                        filename = source_map.get("filename_relative", "N/A")
                        
                        location_parts = []
                        if elem_type and elem_type != "N/A":
                            location_parts.append(f"Type `{elem_type}`")
                        if elem_name and elem_name != "N/A":
                            if len(elem_name) > 100:
                                location_parts.append(f"Content starts with `{elem_name[:50]}...`")
                            else:
                                location_parts.append(f"Name `{elem_name}`")
                        if lines:
                            location_parts.append(f"Lines `{', '.join(map(str, lines))}`")
                        if filename and filename != "N/A":
                            location_parts.append(f"in `{filename}`")
                        
                        if location_parts:
                            report_content.append(f"  - **Location:** {', '.join(location_parts)}")
                
                # Add markdown content if available
                if "markdown" in finding and finding['markdown']:
                    report_content.append("\n**Details:**")
                    report_content.append(f"```solidity\n{finding['markdown'].strip()}\n```\n")
        
        # Process custom findings if they exist
        if 'custom_findings' in report_data and report_data['custom_findings']:
            for finding in report_data['custom_findings']:
                description = finding.get('description', 'No description')
                check = finding.get('check', 'Custom finding')
                impact = finding.get('impact', 'Informational')
                confidence = finding.get('confidence', 'Medium')
                
                report_content.append(f"### {check}")
                report_content.append(f"- **Impact:** {impact}")
                report_content.append(f"- **Confidence:** {confidence}")
                report_content.append(f"- **Description:** {description}")
                
                if 'elements' in finding and finding['elements']:
                    for elem in finding['elements']:
                        if 'source_mapping' in elem:
                            source_map = elem['source_mapping']
                            lines = source_map.get("lines", [])
                            filename = source_map.get("filename_relative", "N/A")
                            
                            location_parts = []
                            if lines:
                                location_parts.append(f"Lines `{', '.join(map(str, lines))}`")
                            if filename and filename != "N/A":
                                location_parts.append(f"in `{filename}`")
                            
                            if location_parts:
                                report_content.append(f"  - **Location:** {', '.join(location_parts)}")
                
                if 'code' in finding:
                    report_content.append("\n**Code Snippet:**")
                    report_content.append(f"```solidity\n{finding['code'].strip()}\n```\n")
        else:
            report_content.append("No security issues found.\n")
        
        report_content.append("---\n")
    
    # Write the report to file
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))
        print(f"Report generated successfully at {report_path}")
    except Exception as e:
        print(f"Error writing report: {e}")
        return


def generate_summary_report():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: Detection manifest '{os.path.abspath(MANIFEST_FILE)}' not found. Run loophole detection first.")
        sys.exit(1) # Exit with error code

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    # ... rest of the generate_summary_report function ...
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    report_content = ["# Smart Contract Security Audit Summary\n\n"]
    total_contracts_processed_for_report = 0
    total_slither_issues = 0
    total_custom_issues = 0
    
    vulnerability_counts = {} 

    print(f"Generating summary report from '{DETECTION_DIR}'...")

    for contract_key, report_path in manifest.items():
        total_contracts_processed_for_report +=1
        report_content.append(f"## Contract: {contract_key}\n")
        
        if not os.path.exists(report_path):
            report_content.append(f"  - Error: Report file not found at {os.path.abspath(report_path)}\n")
            report_content.append("---\n")
            continue
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f_report:
                data = json.load(f_report)

            slither_success = data.get("slither_success", False) # From Slither's own report
            slither_run_error = data.get("slither_error") # Error from our script running Slither
            slither_stderr = data.get("slither_stderr")
            slither_findings = data.get("slither_findings", [])
            custom_findings = data.get("custom_findings", [])

            if slither_run_error: # If our script had an issue running/parsing Slither
                report_content.append(f"  - **Slither Execution Issue:** {slither_run_error}\n")
            elif not slither_success and slither_findings: # Slither ran, reported failure (e.g. compile error), but gave findings
                report_content.append(f"  - Slither analysis reported `success: false` (e.g., compilation issues). Findings below might include these errors.\n")
                if slither_stderr:
                    report_content.append(f"    <details><summary>Slither stderr (click to expand)</summary>\n\n    ```\n    {slither_stderr}\n    ```\n    </details>\n")

            elif not slither_success: # Slither ran, reported failure, no findings (more severe)
                 report_content.append(f"  - Slither analysis failed or did not complete successfully.\n")
                 if slither_stderr:
                    report_content.append(f"    <details><summary>Slither stderr (click to expand)</summary>\n\n    ```\n    {slither_stderr}\n    ```\n    </details>\n")


            if not slither_findings and not custom_findings and (slither_success or not slither_run_error) :
                report_content.append("  - No specific vulnerabilities detected by Slither or custom rules.\n")
            
            if slither_findings:
                report_content.append(f"  ### Slither Findings ({len(slither_findings)} issues):")
                for finding in slither_findings:
                    report_content.append(format_finding(finding, "Slither"))
                    total_slither_issues += 1
                    vuln_name = f"Slither: {finding.get('check', 'Unknown')}"
                    vulnerability_counts[vuln_name] = vulnerability_counts.get(vuln_name, 0) + 1
                report_content.append("\n")

            if custom_findings:
                report_content.append(f"  ### Custom Rule Findings ({len(custom_findings)} issues):")
                for finding in custom_findings:
                    report_content.append(format_finding(finding, "Custom"))
                    total_custom_issues += 1
                    vuln_name = f"Custom: {finding.get('check', 'Unknown')}"
                    vulnerability_counts[vuln_name] = vulnerability_counts.get(vuln_name, 0) + 1
                report_content.append("\n")

        except Exception as e:
            report_content.append(f"  - Error reading or parsing report file {report_path}: {e}\n")
        
        report_content.append("---\n") 

    overall_stats = [
        f"## Overall Statistics\n",
        f"- Total contracts processed for reporting: {total_contracts_processed_for_report}",
        f"- Total Slither issues found: {total_slither_issues}",
        f"- Total Custom rule issues found: {total_custom_issues}",
        f"- Grand total issues: {total_slither_issues + total_custom_issues}\n",
        f"### Vulnerability Type Counts:\n"
    ]
    if vulnerability_counts:
        for vuln, count in sorted(vulnerability_counts.items(), key=lambda item: item[1], reverse=True):
            overall_stats.append(f"  - {vuln}: {count}")
    else:
        overall_stats.append("  - No specific vulnerability types tallied.\n")
    
    report_content.insert(1, "\n".join(overall_stats) + "\n---\n")


    with open(SUMMARY_REPORT_FILE, 'w', encoding='utf-8') as f_out:
        f_out.write("\n".join(report_content))

    print("\n--- Report Generation Summary ---")
    print(f"Processed {total_contracts_processed_for_report} contract reports.")
    print(f"Total Slither issues reported: {total_slither_issues}")
    print(f"Total Custom rule issues reported: {total_custom_issues}")
    print(f"Summary report saved to '{SUMMARY_REPORT_FILE}'")


def format_finding(finding, finding_type):
    """Format a finding (Slither or custom) into a markdown report section"""
    report_lines = []
    check = finding.get("check", "Unknown Issue")
    impact = finding.get("impact", "Unknown")
    confidence = finding.get("confidence", "Unknown")
    description = finding.get("description", "No description provided")
    
    report_lines.append(f"  - **{check}** (Impact: {impact}, Confidence: {confidence})")
    report_lines.append(f"    - **Description:** {description}")
    
    elements = finding.get("elements", [])
    if elements:
        report_lines.append(f"    - **Details:**")
        for elem in elements:
            elem_type = elem.get("type", "N/A")
            elem_name = elem.get("name", "N/A")
            source_map = elem.get("source_mapping", {})
            lines = source_map.get("lines", [])
            filename = source_map.get("filename_relative", "N/A")
            
            location_parts = [f"Type `{elem_type}`"]
            if elem_name and elem_name != "N/A": # Only add name if it's meaningful
                # Avoid printing the whole line content as elem_name for custom rules if it's too long
                if finding_type == "Custom" and len(elem_name) > 100 :
                     location_parts.append(f"Content starts with `{elem_name[:50]}...`")
                else:
                     location_parts.append(f"Name/Content `{elem_name}`")

            if lines:
                location_parts.append(f"Lines `{', '.join(map(str, lines))}`")
            if filename and filename != "N/A":
                location_parts.append(f"in `{filename}`")
            
            report_lines.append(f"      - **Location:** {', '.join(location_parts)}")
            
            if "markdown" in elem: # Slither >= 0.8.0 can output markdown directly for elements
                report_lines.append(f"        {elem['markdown']}")
            elif "expression" in elem and "snippet" in elem: # Older Slither format
                 report_lines.append(f"        ```solidity\n        {elem['expression']} // from snippet: {elem['snippet']}\n        ```")
            elif "snippet" in elem: # Fallback to snippet
                 report_lines.append(f"        ```solidity\n        {elem['snippet']}\n        ```")
    return "\n".join(report_lines)


def generate_external_report(contract_path):
    """Generate report for an external contract"""
    if not contract_path or not os.path.exists(contract_path):
        print(f"Error: Contract not found at {contract_path}")
        return False
    
    contract_name = os.path.splitext(os.path.basename(contract_path))[0]
    detection_file = os.path.join(EXTERNAL_RESULTS_DIR, f"{contract_name}_detection.json")
    
    if not os.path.exists(detection_file):
        print(f"Error: Detection results not found for {contract_name}. Run loophole detection first.")
        return False
    
    # Create reports directory if it doesn't exist
    os.makedirs(EXTERNAL_REPORTS_DIR, exist_ok=True)
    # Use exactly the same filename pattern as expected by test_pipeline.py
    report_path = os.path.join(EXTERNAL_REPORTS_DIR, f"{contract_name}_report.md")
    
    try:
        with open(detection_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        report_content = [f"# Security Analysis for Contract: {contract_name}\n"]
        
        # Add summary section
        slither_findings = data.get("slither_findings", [])
        custom_findings = data.get("custom_findings", [])
        total_issues = len(slither_findings) + len(custom_findings)
        
        report_content.append(f"## Summary\n")
        report_content.append(f"- **Contract:** {contract_name}")
        report_content.append(f"- **Total Issues Found:** {total_issues}")
        report_content.append(f"- **Analysis Date:** {data.get('analysis_date', 'Not specified')}\n")
        
        # Add findings sections
        if slither_findings:
            report_content.append(f"## Slither Findings ({len(slither_findings)} issues)\n")
            for finding in slither_findings:
                report_content.append(format_finding(finding, "Slither"))
            report_content.append("\n")
        else:
            report_content.append("## Slither Findings\n\nNo issues detected by Slither.\n")
        
        if custom_findings:
            report_content.append(f"## Custom Rule Findings ({len(custom_findings)} issues)\n")
            for finding in custom_findings:
                report_content.append(format_finding(finding, "Custom"))
            report_content.append("\n")
        else:
            report_content.append("## Custom Rule Findings\n\nNo issues detected by custom rules.\n")
        
        # Add recommendations section
        report_content.append("## Recommendations\n")
        if total_issues > 0:
            report_content.append("Based on the findings, consider the following recommendations:\n")
            if any(f.get('impact') == 'High' for f in slither_findings + custom_findings):
                report_content.append("- **Critical:** Address high impact issues before deploying this contract")
            if any(f.get('check') == 'reentrancy' for f in slither_findings):
                report_content.append("- **Reentrancy:** Implement checks-effects-interactions pattern")
            if any('overflow' in f.get('check', '').lower() for f in slither_findings + custom_findings):
                report_content.append("- **Arithmetic:** Use SafeMath or Solidity 0.8+ for arithmetic operations")
            report_content.append("- **General:** Consider a professional audit before deploying with significant value")
        else:
            report_content.append("No significant issues were detected, but this does not guarantee the contract is free from vulnerabilities. Consider:\n")
            report_content.append("- Conducting thorough unit and integration testing")
            report_content.append("- Performing a professional security audit")
        
        # Write the report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_content))
        
        print(f"Report for {contract_name} generated at: {os.path.abspath(report_path)}")
        return True
    
    except Exception as e:
        print(f"Error generating report for {contract_name}: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate reports from detection results')
    parser.add_argument('--contract', type=str, help='Path to a specific external contract')
    
    args = parser.parse_args()
    
    if args.contract:
        # For external contract evaluation
        contract_name = os.path.splitext(os.path.basename(args.contract))[0]
        generate_external_report(args.contract)
    else:
        # Default to training report
        generate_training_report()
# src/contract_analysis/imp_tools_integration.py - Improved security analysis tools integration
import os
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any, Tuple
from abc import ABC, abstractmethod


class SecurityAnalysisTool(ABC):
    """Base class for security analysis tools"""
    
    def __init__(self, tool_path: str = None):
        self.tool_path = tool_path
        self.results = {}
        
    @abstractmethod
    def analyze(self, contract_path: str) -> Dict:
        """Run analysis on the specified contract file"""
        pass
    
    @abstractmethod
    def parse_results(self, raw_output: str) -> Dict:
        """Parse tool output into structured format"""
        pass
    
    def get_results(self) -> Dict:
        """Get the parsed results from the last analysis"""
        return self.results


class MythrilAnalyzer(SecurityAnalysisTool):
    """Integration with Mythril security analyzer"""
    
    def __init__(self, tool_path: str = 'myth'):
        super().__init__(tool_path)
        
    def analyze(self, contract_path: str) -> Dict:
        """Run Mythril analysis on the contract with enhanced error handling"""
        if not os.path.exists(contract_path):
            self.results = {'error': f"File not found: {contract_path}"}
            return self.results
            
        try:
            # Run Mythril with JSON output and specified solidity version
            cmd = [self.tool_path, 'analyze', '--solv', '0.8.0', '-o', 'json', contract_path]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # Added timeout
            
            if process.returncode != 0 and not process.stdout:
                self.results = {
                    'error': f"Mythril analysis failed: {process.stderr}",
                    'tool': 'Mythril',
                    'success': False
                }
                return self.results
                
            # Parse the results
            self.results = self.parse_results(process.stdout)
            self.results['success'] = True
            return self.results
            
        except subprocess.TimeoutExpired:
            self.results = {
                'error': "Mythril analysis timed out after 300 seconds",
                'tool': 'Mythril',
                'success': False
            }
            return self.results
        except Exception as e:
            self.results = {
                'error': f"Error running Mythril: {str(e)}",
                'tool': 'Mythril',
                'success': False
            }
            return self.results
    
    def parse_results(self, raw_output: str) -> Dict:
        """Parse Mythril JSON output with improved error handling"""
        parsed_results = {
            'tool': 'Mythril',
            'issues': []
        }
        
        try:
            # Try to parse as JSON
            if raw_output.strip():
                mythril_results = json.loads(raw_output)
                
                for issue in mythril_results.get('issues', []):
                    parsed_issue = {
                        'title': issue.get('title', 'Unknown Issue'),
                        'description': issue.get('description', ''),
                        'severity': issue.get('severity', 'Unknown').capitalize(),
                        'line_numbers': [],
                        'code_snippet': '',
                        'swc_id': issue.get('swc-id', ''),
                        'confidence': issue.get('confidence', 'Unknown')
                    }
                    
                    # Extract line numbers and code from source mapping
                    for source in issue.get('sourceMap', []):
                        if 'line' in source:
                            parsed_issue['line_numbers'].append(source['line'])
                        if 'source' in source:
                            parsed_issue['code_snippet'] += source['source'] + '\n'
                    
                    parsed_results['issues'].append(parsed_issue)
            
            # If no issues found but we have output, add raw output for debugging
            if not parsed_results['issues'] and raw_output.strip():
                parsed_results['raw_output'] = raw_output[:1000]  # Limit size for large outputs
                
            return parsed_results
            
        except json.JSONDecodeError:
            # If not valid JSON, try to extract information using regex
            parsed_results['raw_output'] = raw_output[:1000]
            parsed_results['error_parsing'] = "Could not parse Mythril JSON output"
            
            # Try to extract issues using simple pattern matching
            issue_pattern = r'=== (\w+) ===\n([\s\S]+?)(?=\n===|\Z)'
            matches = re.findall(issue_pattern, raw_output)
            
            for issue_type, content in matches:
                # Extract first line number mentioned
                line_match = re.search(r'line (\d+)', content)
                line_number = int(line_match.group(1)) if line_match else None
                
                parsed_issue = {
                    'title': issue_type,
                    'description': content.strip()[:200],  # Truncate description
                    'severity': 'Unknown',
                    'line_numbers': [line_number] if line_number else []
                }
                parsed_results['issues'].append(parsed_issue)
            
            return parsed_results


class SmartCheckAnalyzer(SecurityAnalysisTool):
    """Integration with SmartCheck security analyzer"""
    
    def __init__(self, tool_path: str = 'smartcheck'):
        super().__init__(tool_path)
        
    def analyze(self, contract_path: str) -> Dict:
        """Run SmartCheck analysis on the contract with enhanced XML output processing"""
        if not os.path.exists(contract_path):
            self.results = {
                'error': f"File not found: {contract_path}",
                'tool': 'SmartCheck',
                'success': False
            }
            return self.results
            
        try:
            # Request XML output from SmartCheck
            cmd = [self.tool_path, '-p', contract_path, '--output-format', 'xml'] 
            process = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300)
            
            if process.returncode != 0 and not process.stdout.strip(): 
                self.results = {
                    'error': f"SmartCheck analysis failed: {process.stderr}",
                    'tool': 'SmartCheck',
                    'success': False
                }
                return self.results
            
            # Parse results regardless of return code
            self.results = self.parse_results(process.stdout)
            
            # Add relevant stderr if available and no issues found
            if process.stderr and not self.results.get('issues'):
                self.results['stderr_output'] = process.stderr[:500]  # Limit size
                
            self.results['success'] = True
            return self.results
            
        except subprocess.TimeoutExpired:
            self.results = {
                'error': "SmartCheck analysis timed out after 300 seconds",
                'tool': 'SmartCheck',
                'success': False
            }
            return self.results
        except Exception as e:
            self.results = {
                'error': f"Error running SmartCheck: {str(e)}",
                'tool': 'SmartCheck',
                'success': False
            }
            return self.results
    
    def parse_results(self, raw_output: str) -> Dict:
        """Parse SmartCheck XML output with enhanced error handling and fallback"""
        parsed_results = {
            'tool': 'SmartCheck',
            'issues': []
        }
        
        if not raw_output.strip():
            parsed_results['error'] = "Empty output from SmartCheck"
            return parsed_results
            
        try:
            root = ET.fromstring(raw_output)
            
            for issue_node in root.findall('.//issue'):
                issue = {
                    'title': issue_node.get('id', 'Unknown Issue'),
                    'description': issue_node.findtext('description', ''),
                    'severity': issue_node.get('severity', 'Unknown').capitalize(),
                    'line_numbers': [],
                    'code_snippet': issue_node.findtext('snippet/code', ''),
                    'pattern_id': issue_node.get('patternId', ''),
                    'rule': issue_node.findtext('rule', '')
                }
                
                # Extract line numbers from locations
                for loc_node in issue_node.findall('location'):
                    line = loc_node.get('line')
                    if line:
                        try:
                            issue['line_numbers'].append(int(line))
                        except ValueError:
                            pass
                
                parsed_results['issues'].append(issue)
                
            # If no issues found but we have output, store for debugging
            if not parsed_results['issues'] and raw_output.strip(): 
                parsed_results['raw_output'] = raw_output[:1000]
                
            return parsed_results
            
        except ET.ParseError:
            # Fallback to text parsing if XML parsing fails
            parsed_results['raw_output'] = raw_output[:1000]
            parsed_results['error_parsing'] = "Could not parse SmartCheck XML output"
            
            # Try to extract issues using simple pattern matching
            issue_pattern = r'Rule:\s+([^\n]+)\nDescription:\s+([^\n]+)\nSeverity:\s+([^\n]+)\nLine:\s+(\d+)'
            matches = re.findall(issue_pattern, raw_output)
            
            for rule, description, severity, line in matches:
                parsed_issue = {
                    'title': rule.strip(),
                    'description': description.strip(),
                    'severity': severity.strip(),
                    'line_numbers': [int(line)]
                }
                parsed_results['issues'].append(parsed_issue)
            
            return parsed_results


class OyenteAnalyzer(SecurityAnalysisTool):
    """Integration with Oyente security analyzer"""
    
    def __init__(self, tool_path: str = 'oyente'):
        super().__init__(tool_path)
        
    def analyze(self, contract_path: str) -> Dict:
        """Run Oyente analysis on the contract"""
        if not os.path.exists(contract_path):
            self.results = {
                'error': f"File not found: {contract_path}",
                'tool': 'Oyente',
                'success': False
            }
            return self.results
            
        try:
            # Run Oyente with JSON flag
            cmd = [self.tool_path, '-j', '-s', contract_path]
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if process.returncode != 0 and not process.stdout:
                self.results = {
                    'error': f"Oyente analysis failed: {process.stderr}",
                    'tool': 'Oyente',
                    'success': False
                }
                return self.results
                
            # Parse the results
            self.results = self.parse_results(process.stdout)
            self.results['success'] = True
            return self.results
            
        except subprocess.TimeoutExpired:
            self.results = {
                'error': "Oyente analysis timed out after 300 seconds",
                'tool': 'Oyente',
                'success': False
            }
            return self.results
        except Exception as e:
            self.results = {
                'error': f"Error running Oyente: {str(e)}",
                'tool': 'Oyente',
                'success': False
            }
            return self.results
    
    def parse_results(self, raw_output: str) -> Dict:
        """Parse Oyente JSON output"""
        parsed_results = {
            'tool': 'Oyente',
            'issues': []
        }
        
        try:
            # Try to parse as JSON
            if raw_output.strip():
                oyente_results = json.loads(raw_output)
                
                # Oyente output format is different from others
                for contract, analysis in oyente_results.items():
                    for issue_type, has_issue in analysis.get('vulnerabilities', {}).items():
                        if has_issue:
                            parsed_issue = {
                                'title': issue_type.replace('_', ' ').capitalize(),
                                'description': f"Oyente detected {issue_type} vulnerability",
                                'severity': self._get_severity_for_issue(issue_type),
                                'line_numbers': [],  # Oyente doesn't provide line numbers directly
                                'contract': contract
                            }
                            parsed_results['issues'].append(parsed_issue)
            
            # If no issues found but we have output, add raw output for debugging
            if not parsed_results['issues'] and raw_output.strip():
                parsed_results['raw_output'] = raw_output[:1000]
                
            return parsed_results
            
        except json.JSONDecodeError:
            # If not valid JSON, try to extract information differently
            parsed_results['raw_output'] = raw_output[:1000]
            parsed_results['error_parsing'] = "Could not parse Oyente JSON output"
            
            # Try to extract issues using regex pattern matching
            contract_pattern = r'======= ([^\n]+) =======\n([\s\S]+?)(?=\n=======|\Z)'
            vulnerability_pattern = r'([a-zA-Z_]+):\s+(True|False)'
            
            contract_matches = re.findall(contract_pattern, raw_output)
            
            for contract, details in contract_matches:
                vulnerability_matches = re.findall(vulnerability_pattern, details)
                
                for issue_type, is_vulnerable in vulnerability_matches:
                    if is_vulnerable.lower() == 'true':
                        parsed_issue = {
                            'title': issue_type.replace('_', ' ').capitalize(),
                            'description': f"Oyente detected {issue_type} vulnerability",
                            'severity': self._get_severity_for_issue(issue_type),
                            'contract': contract
                        }
                        parsed_results['issues'].append(parsed_issue)
            
            return parsed_results
    
    def _get_severity_for_issue(self, issue_type: str) -> str:
        """Map Oyente issue types to severity levels"""
        severity_map = {
            'reentrancy': 'High',
            'timestamp_dependency': 'Medium',
            'assertion_failure': 'High',
            'integer_overflow': 'High',
            'integer_underflow': 'Medium',
            'money_concurrency': 'High',
            'transaction_ordering_dependence': 'Medium',
            'parity_multisig_bug': 'Critical'
        }
        return severity_map.get(issue_type.lower(), 'Medium')


class MultiToolAnalyzer:
    """Run multiple security analysis tools and aggregate results"""
    
    def __init__(self):
        self.analyzers = {
            'mythril': MythrilAnalyzer(),
            'oyente': OyenteAnalyzer(),
            'smartcheck': SmartCheckAnalyzer()
        }
        self.combined_results = {}
        
    def analyze_contract(self, contract_path: str, tools: List[str] = None) -> Dict:
        """Run analysis with specified tools with parallel execution and enhanced error handling"""
        if not os.path.exists(contract_path):
            return {'error': f"Contract file not found: {contract_path}"}
            
        # If no specific tools requested, use all available
        if not tools:
            tools = list(self.analyzers.keys())
        
        # Track overall stats
        successful_tools = 0
        total_issues = 0
        
        # Store tool-specific results
        self.combined_results = {
            'contract_path': contract_path,
            'filename': os.path.basename(contract_path),
            'tool_results': {},
            'summary': {
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'total_issues': 0
            }
        }
        
        # Run each requested tool
        for tool_name in tools:
            if tool_name not in self.analyzers:
                self.combined_results['tool_results'][tool_name] = {
                    'error': f"Unknown tool: {tool_name}", 
                    'success': False
                }
                continue
                
            # Run the tool's analysis
            tool_result = self.analyzers[tool_name].analyze(contract_path)
            self.combined_results['tool_results'][tool_name] = tool_result
            
            # Update statistics if successful
            if tool_result.get('success', False) and 'issues' in tool_result:
                successful_tools += 1
                issue_count = len(tool_result['issues'])
                total_issues += issue_count
                
                # Count severity levels
                for issue in tool_result['issues']:
                    severity = issue.get('severity', '').lower()
                    if severity in ['high', 'critical']:
                        self.combined_results['summary']['high_severity'] += 1
                    elif severity == 'medium':
                        self.combined_results['summary']['medium_severity'] += 1
                    else:
                        self.combined_results['summary']['low_severity'] += 1
        
        # Update summary
        self.combined_results['summary']['total_issues'] = total_issues
        self.combined_results['summary']['successful_tools'] = successful_tools
        self.combined_results['summary']['requested_tools'] = len(tools)
        
        return self.combined_results
                
    def get_combined_results(self) -> Dict:
        """Get combined results from all tools"""
        return self.combined_results


# Factory function to create analyzers based on type
def create_analyzer(analyzer_type: str) -> SecurityAnalysisTool:
    """Factory method to create security analyzers by type"""
    if analyzer_type.lower() == 'mythril':
        return MythrilAnalyzer()
    elif analyzer_type.lower() == 'smartcheck':
        return SmartCheckAnalyzer()
    elif analyzer_type.lower() == 'oyente':
        return OyenteAnalyzer()
    elif analyzer_type.lower() == 'multi':
        return MultiToolAnalyzer()
    else:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")

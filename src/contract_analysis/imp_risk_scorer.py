# src/contract_analysis/imp_risk_scorer.py - Improved risk scoring module
import numpy as np
import re
import json
import os
from typing import Dict, List, Any, Tuple
from enum import Enum

class RiskLevel(Enum):
    """Risk level enumeration with enhanced clarity"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    @classmethod
    def to_string(cls, level):
        """Convert risk level to human-readable string"""
        return {
            cls.NONE: "None",
            cls.LOW: "Low", 
            cls.MEDIUM: "Medium",
            cls.HIGH: "High",
            cls.CRITICAL: "Critical"
        }.get(level, "Unknown")
    
    @classmethod
    def from_string(cls, level_str):
        """Convert string to risk level enum with case insensitivity"""
        level_map = {
            "none": cls.NONE,
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "critical": cls.CRITICAL
        }
        return level_map.get(level_str.lower(), cls.LOW)  # Default to LOW if unknown


class RiskScore:
    """Container for risk assessment results with enhanced reporting"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.total_score = 0
        self.max_risk_level = RiskLevel.NONE
        self.risk_categories = {}
        
    def add_vulnerability(self, name: str, description: str, risk_level: RiskLevel, 
                         category: str, location: str = None, remediation: str = None):
        """Add a vulnerability finding to the risk assessment"""
        vuln = {
            'name': name,
            'description': description,
            'risk_level': risk_level,
            'risk_level_str': RiskLevel.to_string(risk_level),
            'category': category,
            'location': location,
            'remediation': remediation
        }
        
        self.vulnerabilities.append(vuln)
        
        # Update max risk level
        if risk_level.value > self.max_risk_level.value:
            self.max_risk_level = risk_level
            
        # Update category stats
        if category not in self.risk_categories:
            self.risk_categories[category] = {
                'count': 0,
                'max_level': RiskLevel.NONE,
                'score': 0
            }
        
        self.risk_categories[category]['count'] += 1
        if risk_level.value > self.risk_categories[category]['max_level'].value:
            self.risk_categories[category]['max_level'] = risk_level
        
        # Update score
        weight = self._get_risk_weight(risk_level)
        self.risk_categories[category]['score'] += weight
        self.total_score += weight
        
    def _get_risk_weight(self, level: RiskLevel) -> int:
        """Convert risk level to numerical weight"""
        weights = {
            RiskLevel.NONE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 7,
            RiskLevel.CRITICAL: 15
        }
        return weights.get(level, 0)
        
    def get_overall_risk_level(self) -> RiskLevel:
        """Determine overall risk level based on total score"""
        if self.total_score == 0:
            return RiskLevel.NONE
        elif self.total_score < 3:
            return RiskLevel.LOW
        elif self.total_score < 8:
            return RiskLevel.MEDIUM
        elif self.total_score < 18:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
            
    def get_summary(self) -> Dict:
        """Get summary of risk assessment with enhanced details"""
        vulnerability_count = len(self.vulnerabilities)
        
        # Count vulnerabilities by level
        level_counts = {level: 0 for level in RiskLevel}
        for vuln in self.vulnerabilities:
            level_counts[vuln['risk_level']] += 1
            
        overall_level = self.get_overall_risk_level()
        
        summary = {
            'total_score': self.total_score,
            'overall_risk_level': overall_level,
            'overall_risk_str': RiskLevel.to_string(overall_level),
            'vulnerability_count': vulnerability_count,
            'risk_distribution': {
                'none': level_counts[RiskLevel.NONE],
                'low': level_counts[RiskLevel.LOW],
                'medium': level_counts[RiskLevel.MEDIUM],
                'high': level_counts[RiskLevel.HIGH],
                'critical': level_counts[RiskLevel.CRITICAL]
            },
            'categories': {}
        }
        
        # Add category summaries
        for category, stats in self.risk_categories.items():
            summary['categories'][category] = {
                'count': stats['count'],
                'max_level': RiskLevel.to_string(stats['max_level']),
                'score': stats['score']
            }
            
        return summary
    
    def get_detailed_report(self) -> Dict:
        """Get detailed risk report including all vulnerabilities"""
        return {
            'summary': self.get_summary(),
            'vulnerabilities': self.vulnerabilities
        }


class RiskScorer:
    """Base class for risk scoring"""
    
    def __init__(self):
        self.risk_score = RiskScore()
    
    def get_risk_score(self) -> RiskScore:
        """Get the current risk score"""
        return self.risk_score
        
    def reset(self):
        """Reset the risk score"""
        self.risk_score = RiskScore()


class LegalContractRiskScorer(RiskScorer):
    """Risk scorer for legal contracts with configuration-based pattern matching"""
    
    def __init__(self, patterns_file: str = 'config/legal_risk_patterns.json'):
        super().__init__()
        # Risk patterns to look for
        self.risk_patterns = self._load_risk_patterns(patterns_file)
        
    def _load_risk_patterns(self, patterns_file: str) -> Dict:
        """Load risk patterns for legal contract analysis from configuration"""
        default_patterns = {
            'missing_clauses': {
                'termination': {
                    'keywords': ['termination', 'terminate', 'end of agreement'],
                    'regex_patterns': [r'(?i)termination\s+clause'],
                    'risk_level': RiskLevel.HIGH,
                    'description': 'Missing or inadequate termination clause',
                    'category': 'Completeness',
                    'remediation': 'Add a clear termination clause that specifies conditions and process.'
                },
                'confidentiality': {
                    'keywords': ['confidential', 'confidentiality', 'non-disclosure'],
                    'regex_patterns': [r'(?i)confidential\s+information'],
                    'risk_level': RiskLevel.MEDIUM,
                    'description': 'Missing confidentiality clause',
                    'category': 'Completeness',
                    'remediation': 'Add a comprehensive confidentiality clause.'
                },
                'liability': {
                    'keywords': ['liability', 'indemnification', 'indemnify'],
                    'regex_patterns': [r'(?i)limitation\s+of\s+liability'],
                    'risk_level': RiskLevel.HIGH,
                    'description': 'Missing liability clause',
                    'category': 'Completeness',
                    'remediation': 'Add a liability clause that clearly defines limits.'
                }
            },
            'ambiguous_terms': {
                'reasonable': {
                    'keywords': ['reasonable'],
                    'regex_patterns': [r'(?i)reasonable\s+(?:efforts|time|notice)'],
                    'risk_level': RiskLevel.MEDIUM,
                    'description': 'Use of ambiguous term "reasonable"',
                    'category': 'Clarity',
                    'remediation': 'Define specific criteria or metrics instead of using subjective terms.'
                },
                'substantial': {
                    'keywords': ['substantial', 'substantially'],
                    'regex_patterns': [r'(?i)substantial\s+(?:completion|performance)'],
                    'risk_level': RiskLevel.MEDIUM,
                    'description': 'Use of ambiguous term "substantial"',
                    'category': 'Clarity',
                    'remediation': 'Define specific criteria for completion or performance.'
                }
            }
        }
        
        try:
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    loaded_patterns = json.load(f)
                    
                # Convert risk_level strings to RiskLevel enum members
                for category_key, category_val in loaded_patterns.items():
                    for pattern_key, pattern_val in category_val.items():
                        if 'risk_level' in pattern_val and isinstance(pattern_val['risk_level'], str):
                            try:
                                pattern_val['risk_level'] = RiskLevel[pattern_val['risk_level'].upper()]
                            except KeyError:
                                print(f"Warning: Invalid risk level '{pattern_val['risk_level']}' in {patterns_file}. Defaulting to LOW.")
                                pattern_val['risk_level'] = RiskLevel.LOW
                                
                return loaded_patterns
            else:
                print(f"Warning: Risk patterns file not found: {patterns_file}. Using default patterns.")
                return default_patterns
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Error loading risk patterns from {patterns_file}: {str(e)}. Using default patterns.")
            return default_patterns
            
    def analyze_contract(self, contract_text: str) -> RiskScore:
        """Analyze legal contract for risks using configuration-based pattern matching"""
        if not contract_text:
            self.risk_score.add_vulnerability(
                name="Empty contract",
                description="The contract text is empty or could not be extracted",
                risk_level=RiskLevel.CRITICAL,
                category="Completeness",
                remediation="Provide a valid contract document with proper text content."
            )
            return self.risk_score
        
        # Check for missing important clauses
        self._check_missing_clauses(contract_text)
        
        # Check for ambiguous terms
        self._check_ambiguous_terms(contract_text)
        
        # Check for unbalanced rights and obligations
        self._check_unbalanced_rights(contract_text)
        
        return self.risk_score
    
    def _check_missing_clauses(self, contract_text: str):
        """Check for missing important clauses using pattern matching from configuration"""
        contract_text_lower = contract_text.lower()
        missing_clauses_patterns = self.risk_patterns.get('missing_clauses', {})

        for clause_id, clause_info in missing_clauses_patterns.items():
            found = False
            
            # Check keywords
            if any(keyword.lower() in contract_text_lower for keyword in clause_info.get('keywords', [])):
                found = True
                
            # Check regex patterns if keywords not found
            if not found and clause_info.get('regex_patterns'):
                if any(re.search(pattern, contract_text) for pattern in clause_info.get('regex_patterns', [])):
                    found = True
            
            if not found:
                self.risk_score.add_vulnerability(
                    name=f"Missing {clause_id.replace('_', ' ')} clause",
                    description=clause_info.get('description', f"Missing {clause_id} clause"),
                    risk_level=clause_info.get('risk_level', RiskLevel.MEDIUM),
                    category=clause_info.get('category', 'Completeness'),
                    remediation=clause_info.get('remediation', f"Add a {clause_id} clause to the contract.")
                )
    
    def _check_ambiguous_terms(self, contract_text: str):
        """Check for ambiguous terms using pattern matching from configuration"""
        ambiguous_terms_patterns = self.risk_patterns.get('ambiguous_terms', {})
        
        for term_id, term_info in ambiguous_terms_patterns.items():
            # Check keywords with context
            for keyword in term_info.get('keywords', []):
                # Find all occurrences with surrounding context
                keyword_lower = keyword.lower()
                contract_lower = contract_text.lower()
                
                start_pos = 0
                while True:
                    pos = contract_lower.find(keyword_lower, start_pos)
                    if pos == -1:
                        break
                        
                    # Extract some context around the term
                    context_start = max(0, pos - 50)
                    context_end = min(len(contract_text), pos + len(keyword) + 50)
                    context = contract_text[context_start:context_end]
                    
                    self.risk_score.add_vulnerability(
                        name=f"Ambiguous term: {keyword}",
                        description=term_info.get('description', f"Use of potentially ambiguous term: {keyword}"),
                        risk_level=term_info.get('risk_level', RiskLevel.MEDIUM),
                        category=term_info.get('category', 'Clarity'),
                        location=f"...{context}...",
                        remediation=term_info.get('remediation', f"Replace ambiguous term '{keyword}' with more specific language.")
                    )
                    
                    start_pos = pos + len(keyword)
            
            # Check regex patterns
            for pattern in term_info.get('regex_patterns', []):
                for match in re.finditer(pattern, contract_text):
                    # Extract context around the match
                    match_start, match_end = match.span()
                    context_start = max(0, match_start - 30)
                    context_end = min(len(contract_text), match_end + 30)
                    context = contract_text[context_start:context_end]
                    
                    self.risk_score.add_vulnerability(
                        name=f"Ambiguous pattern: {match.group(0)}",
                        description=term_info.get('description', f"Use of potentially ambiguous pattern"),
                        risk_level=term_info.get('risk_level', RiskLevel.MEDIUM),
                        category=term_info.get('category', 'Clarity'),
                        location=f"...{context}...",
                        remediation=term_info.get('remediation', "Replace ambiguous terms with more specific language.")
                    )
    
    def _check_unbalanced_rights(self, contract_text: str):
        """Check for unbalanced rights and obligations between parties"""
        # This is an enhanced heuristic check for unbalanced contracts
        
        # Look for one-sided clauses that benefit only one party
        rights_patterns = {
            'termination_rights': {
                'patterns': [
                    r'(?i)only\s+[\w\s]+\s+may\s+terminate', 
                    r'(?i)right\s+to\s+terminate\s+at\s+any\s+time\s+without\s+(?:reason|cause|notice)'
                ],
                'risk_level': RiskLevel.HIGH,
                'description': 'Unbalanced termination rights',
                'category': 'Fairness',
                'remediation': 'Consider adding reciprocal termination rights to ensure fairness.'
            },
            'liability_caps': {
                'patterns': [
                    r'(?i)([\w\s]+)\s+shall\s+not\s+be\s+liable', 
                    r'(?i)liability\s+of\s+([\w\s]+)\s+is\s+limited'
                ],
                'risk_level': RiskLevel.MEDIUM,
                'description': 'Potentially unbalanced liability limitations',
                'category': 'Fairness',
                'remediation': 'Consider balanced liability provisions for both parties.'
            },
            'indemnification': {
                'patterns': [
                    r'(?i)([\w\s]+)\s+shall\s+indemnify', 
                    r'(?i)indemnification\s+by\s+([\w\s]+)'
                ],
                'risk_level': RiskLevel.MEDIUM,
                'description': 'One-sided indemnification obligations',
                'category': 'Fairness',
                'remediation': 'Consider mutual indemnification provisions where appropriate.'
            }
        }
        
        # Check for each unbalanced rights pattern
        for right_id, right_info in rights_patterns.items():
            matches_by_party = {}
            
            for pattern in right_info['patterns']:
                for match in re.finditer(pattern, contract_text):
                    # Extract the clause with some context
                    match_start, match_end = match.span()
                    context_start = max(0, match_start - 50)
                    context_end = min(len(contract_text), match_end + 50)
                    context = contract_text[context_start:context_end]
                    
                    # Try to identify the party mentioned
                    party = None
                    if match.groups():
                        party = match.group(1).strip()
                    
                    if party:
                        if party not in matches_by_party:
                            matches_by_party[party] = 0
                        matches_by_party[party] += 1
                    
                    self.risk_score.add_vulnerability(
                        name=f"Potentially unbalanced {right_id.replace('_', ' ')}",
                        description=right_info['description'] + (f" favoring {party}" if party else ""),
                        risk_level=right_info['risk_level'],
                        category=right_info['category'],
                        location=f"...{context}...",
                        remediation=right_info['remediation']
                    )
            
            # If we found multiple parties with the same right, check if it's balanced
            if len(matches_by_party) > 1:
                # Check if one party has significantly more rights than others
                counts = list(matches_by_party.values())
                if max(counts) > 2 * min(counts):
                    max_party = max(matches_by_party.items(), key=lambda x: x[1])[0]
                    self.risk_score.add_vulnerability(
                        name=f"Unbalanced {right_id.replace('_', ' ')}",
                        description=f"Rights are unbalanced, favoring {max_party}",
                        risk_level=right_info['risk_level'],
                        category=right_info['category'],
                        remediation=f"Review contract to ensure {right_id.replace('_', ' ')} are balanced between parties."
                    )


class SmartContractRiskScorer(RiskScorer):
    """Risk scorer for smart contracts with enhanced security pattern detection"""
    
    def __init__(self):
        super().__init__()
        # Common vulnerability patterns
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        
    def _load_vulnerability_patterns(self) -> Dict:
        """Load smart contract vulnerability patterns"""
        return {
            'reentrancy': {
                'patterns': [
                    r'\.call\{value:\s*\w+\}\(', 
                    r'\.call\.value\(\w+\)'
                ],
                'risk_level': RiskLevel.HIGH,
                'description': 'Potential reentrancy vulnerability',
                'category': 'Security',
                'remediation': 'Use ReentrancyGuard or Checks-Effects-Interactions pattern.'
            },
            'unchecked_return': {
                'patterns': [
                    r'\.call\{.+\}\([^;]+(?!\s*require)'
                ],
                'risk_level': RiskLevel.MEDIUM,
                'description': 'Unchecked return value from external call',
                'category': 'Security',
                'remediation': 'Check return values with require() statements.'
            },
            'tx_origin': {
                'patterns': [
                    r'tx\.origin\s*==', 
                    r'require\(\s*tx\.origin\s*=='
                ],
                'risk_level': RiskLevel.HIGH,
                'description': 'Using tx.origin for authorization',
                'category': 'Security',
                'remediation': 'Use msg.sender instead of tx.origin for authorization checks.'
            },
            'timestamp_dependency': {
                'patterns': [
                    r'block\.timestamp', 
                    r'now\s*[<>=]'
                ],
                'risk_level': RiskLevel.MEDIUM,
                'description': 'Timestamp dependency',
                'category': 'Security',
                'remediation': 'Avoid using block.timestamp for critical logic.'
            },
            'integer_overflow': {
                'patterns': [
                    r'\w+\s*\+=\s*\w+(?!.*SafeMath)', 
                    r'\w+\s*\+\s*\w+(?!.*SafeMath)'
                ],
                'risk_level': RiskLevel.MEDIUM,
                'description': 'Potential integer overflow/underflow',
                'category': 'Security',
                'remediation': 'Use SafeMath library or Solidity 0.8.0+ built-in overflow checks.'
            }
        }
        
    def analyze_contract_code(self, contract_code: str) -> RiskScore:
        """Analyze smart contract code for vulnerabilities"""
        if not contract_code:
            self.risk_score.add_vulnerability(
                name="Empty contract code",
                description="The contract code is empty",
                risk_level=RiskLevel.CRITICAL,
                category="Completeness",
                remediation="Provide valid contract code."
            )
            return self.risk_score
        
        # Check for known vulnerability patterns
        self._check_vulnerability_patterns(contract_code)
        
        # Analyze gas usage patterns
        self._analyze_gas_usage(contract_code)
        
        # Check adherence to best practices
        self._check_best_practices(contract_code)
        
        return self.risk_score
    
    def _check_vulnerability_patterns(self, contract_code: str):
        """Check for known vulnerability patterns in smart contract code"""
        for vuln_id, vuln_info in self.vulnerability_patterns.items():
            for pattern in vuln_info['patterns']:
                for match in re.finditer(pattern, contract_code):
                    # Extract the vulnerable code with context
                    match_start, match_end = match.span()
                    
                    # Find the beginning of the line
                    line_start = contract_code.rfind('\n', 0, match_start) + 1
                    if line_start == 0:  # If not found or at the beginning
                        line_start = max(0, match_start - 40)
                    
                    # Find the end of the line
                    line_end = contract_code.find('\n', match_end)
                    if line_end == -1:  # If not found
                        line_end = min(len(contract_code), match_end + 40)
                    
                    # Extract context
                    context = contract_code[line_start:line_end].strip()
                    
                    # Try to get line number for better reference
                    line_number = contract_code[:match_start].count('\n') + 1
                    
                    self.risk_score.add_vulnerability(
                        name=f"{vuln_info.get('description', vuln_id)}",
                        description=f"{vuln_info.get('description', 'Potential vulnerability')} detected at line {line_number}",
                        risk_level=vuln_info.get('risk_level', RiskLevel.MEDIUM),
                        category=vuln_info.get('category', 'Security'),
                        location=f"Line {line_number}: {context}",
                        remediation=vuln_info.get('remediation', 'Review and fix this potential vulnerability.')
                    )
    
    def _analyze_gas_usage(self, contract_code: str):
        """Analyze contract for gas optimization issues"""
        # Check for gas-intensive loops
        for match in re.finditer(r'for\s*\([^;]+;[^;]+;[^\)]+\)\s*\{', contract_code):
            match_start, match_end = match.span()
            line_number = contract_code[:match_start].count('\n') + 1
            
            # Extract loop context
            context_start = max(0, match_start - 20)
            context_end = min(len(contract_code), match_end + 40)
            context = contract_code[context_start:context_end]
            
            # Check if the loop contains storage operations
            loop_body_end = self._find_closing_brace(contract_code, match_end)
            loop_body = contract_code[match_end:loop_body_end] if loop_body_end != -1 else contract_code[match_end:match_end+200]
            
            if re.search(r'\w+\s*\[.+\]\s*=', loop_body):  # Storage writes in loop
                self.risk_score.add_vulnerability(
                    name="Gas-intensive storage operations in loop",
                    description="Loop contains storage write operations which can be gas-intensive",
                    risk_level=RiskLevel.MEDIUM,
                    category="Gas Optimization",
                    location=f"Line {line_number}: {context}",
                    remediation="Consider optimizing storage access patterns or using memory variables within loops."
                )
        
        # Check for unnecessary storage usage
        for match in re.finditer(r'\bstruct\b[^{]*\{([^}]*)\}', contract_code, re.DOTALL):
            if match.group(1).count(';') > 10:  # Large struct with many fields
                match_start, match_end = match.span()
                line_number = contract_code[:match_start].count('\n') + 1
                self.risk_score.add_vulnerability(
                    name="Large struct definition",
                    description=f"Large struct definition at line {line_number} may use excessive storage",
                    risk_level=RiskLevel.LOW,
                    category="Gas Optimization",
                    location=f"Line {line_number}",
                    remediation="Consider breaking large structs into smaller, logically grouped structs."
                )
    
    def _check_best_practices(self, contract_code: str):
        """Check for adherence to smart contract best practices"""
        # Check for missing access control
        function_patterns = list(re.finditer(r'function\s+(\w+)\s*\([^\)]*\)\s*(public|external)(?!\s+view|\s+pure|\s+constant)(?!.*onlyOwner|.*require\(|.*\bif\b)', contract_code))
        
        for match in function_patterns:
            function_name = match.group(1)
            if function_name.lower() not in ['constructor', 'initialize', 'fallback', 'receive']:
                match_start, match_end = match.span()
                line_number = contract_code[:match_start].count('\n') + 1
                
                # Get some context around the function declaration
                context_start = max(0, match_start - 20)
                context_end = min(len(contract_code), match_end + 40)
                context = contract_code[context_start:context_end]
                
                self.risk_score.add_vulnerability(
                    name="Missing access control",
                    description=f"Function '{function_name}' may lack proper access control",
                    risk_level=RiskLevel.MEDIUM,
                    category="Security",
                    location=f"Line {line_number}: {context}",
                    remediation="Add access modifiers (e.g., onlyOwner) or explicit checks for authorization."
                )
        
        # Check for missing events for state changes
        state_change_patterns = list(re.finditer(r'(\w+)\s*\[.+\]\s*=', contract_code))
        event_emissions = set(re.findall(r'emit\s+(\w+)\s*\(', contract_code))
        
        # Track variable names that have state changes
        state_vars_changed = set()
        for match in state_change_patterns:
            var_name = match.group(1)
            state_vars_changed.add(var_name)
        
        # If we have state changes but few or no events, flag it
        if len(state_vars_changed) > 2 and len(event_emissions) < len(state_vars_changed) / 2:
            self.risk_score.add_vulnerability(
                name="Insufficient event emissions",
                description="Contract appears to make state changes without emitting sufficient events",
                risk_level=RiskLevel.LOW,
                category="Best Practices",
                remediation="Emit events for important state changes to improve contract observability."
            )
    
    def _find_closing_brace(self, text: str, start_pos: int) -> int:
        """Helper method to find the closing brace matching an opening brace"""
        stack = 0
        for i in range(start_pos, len(text)):
            if text[i] == '{':
                stack += 1
            elif text[i] == '}':
                stack -= 1
                if stack == 0:
                    return i
        return -1  # Not found

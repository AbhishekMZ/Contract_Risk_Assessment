from typing import List, Dict, Any
import re
from pathlib import Path

class VulnerabilityDetector:
    """Base class for vulnerability detectors"""
    
    def __init__(self):
        self.name = "Base Detector"
        self.description = "Base class for all vulnerability detectors"
    
    def detect(self, contract_path: str, contract_content: str) -> List[Dict[str, Any]]:
        """Detect vulnerabilities in the given contract"""
        raise NotImplementedError("Subclasses must implement this method")


class ReentrancyDetector(VulnerabilityDetector):
    """Detects reentrancy vulnerabilities in Solidity contracts"""
    
    def __init__(self):
        super().__init__()
        self.name = "Reentrancy Detector"
        self.description = "Detects reentrancy vulnerabilities in Solidity contracts"
    
    def detect(self, contract_path: str, contract_content: str) -> List[Dict[str, Any]]:
        """Detect reentrancy vulnerabilities"""
        findings = []
        
        # Simple pattern matching for external calls followed by state changes
        # This is a simplified example - a real implementation would use AST analysis
        external_call_patterns = [
            r'\.(call|send|transfer)\s*\(',
            r'\b(?:msg\.sender|tx\.origin)\.call\b',
        ]
        
        state_change_patterns = [
            r'\b(?:balances|mapping|array)\[[^\]]+\]\s*[+-]?=',
            r'\b(?:balances|mapping|array)\[[^\]]+\]\s*=\s*',
        ]
        
        for i, line in enumerate(contract_content.split('\n'), 1):
            if any(re.search(pattern, line) for pattern in external_call_patterns):
                findings.append({
                    'line': i,
                    'severity': 'high',
                    'pattern': 'external_call',
                    'description': 'Potential external call that could lead to reentrancy',
                    'recommendation': 'Use the Checks-Effects-Interactions pattern and consider using ReentrancyGuard'
                })
        
        return findings


class IntegerOverflowDetector(VulnerabilityDetector):
    """Detects integer overflow/underflow vulnerabilities"""
    
    def __init__(self):
        super().__init__()
        self.name = "Integer Overflow Detector"
        self.description = "Detects potential integer overflows/underflows in arithmetic operations"
    
    def detect(self, contract_path: str, contract_content: str) -> List[Dict[str, Any]]:
        findings = []
        
        # Look for arithmetic operations without SafeMath or unchecked blocks
        arithmetic_ops = ['+', '-', '*', '/', '**', '%', '<<', '>>', '|', '&', '^']
        
        for i, line in enumerate(contract_content.split('\n'), 1):
            if any(op in line for op in arithmetic_ops):
                # Skip if SafeMath is being used
                if 'SafeMath' in line or 'using SafeMath' in contract_content:
                    continue
                    
                findings.append({
                    'line': i,
                    'severity': 'high',
                    'pattern': 'arithmetic_operation',
                    'description': 'Potential integer overflow/underflow in arithmetic operation',
                    'recommendation': 'Use SafeMath or Solidity 0.8+ with built-in overflow checks'
                })
        
        return findings


class AccessControlDetector(VulnerabilityDetector):
    """Detects access control issues"""
    
    def __init__(self):
        super().__init__()
        self.name = "Access Control Detector"
        self.description = "Detects missing or insufficient access controls"
    
    def detect(self, contract_path: str, contract_content: str) -> List[Dict[str, Any]]:
        findings = []
        
        # Look for public/external functions without access control
        function_pattern = r'(?:function|constructor)\s+(\w+)\s*\('
        
        # Check for common access control patterns
        has_access_control = any(keyword in contract_content 
                              for keyword in ['onlyOwner', 'onlyRole', 'require(msg.sender == owner)'])
        
        if not has_access_control:
            findings.append({
                'line': 0,
                'severity': 'medium',
                'pattern': 'missing_access_control',
                'description': 'No access control detected on critical functions',
                'recommendation': 'Implement access control using OpenZeppelin AccessControl or Ownable'
            })
        
        return findings


def get_all_detectors() -> List[VulnerabilityDetector]:
    """Return a list of all available detectors"""
    return [
        ReentrancyDetector(),
        IntegerOverflowDetector(),
        AccessControlDetector(),
    ]

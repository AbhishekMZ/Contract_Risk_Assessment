# src/contract_analysis/pipeline.py
import os
import json
import pandas as pd
from typing import Dict, List, Any, Union, Tuple
from pathlib import Path

# NLP libraries
import nltk
import spacy
from transformers import BertTokenizer, BertForSequenceClassification, pipeline

# Smart contract analysis
from web3 import Web3
from solidity_parser import parser

class ContractParser:
    """Base class for contract parsing with common functionality"""
    
    def __init__(self):
        self.contract_text = None
        self.contract_metadata = {}
        self.parsed_sections = {}
        
    def load_contract(self, file_path: str) -> bool:
        """Load contract from file"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
                
            self.contract_metadata['file_path'] = file_path
            self.contract_metadata['file_type'] = file_ext
            
            return True
        except Exception as e:
            print(f"Error loading contract: {str(e)}")
            return False
    
    def extract_metadata(self) -> Dict:
        """Extract metadata from the contract"""
        return self.contract_metadata
        
    def get_parsed_sections(self) -> Dict:
        """Return parsed contract sections"""
        return self.parsed_sections


class LegalContractParser(ContractParser):
    """Parser for traditional legal contracts (PDF, DOC, etc.)"""
    
    def __init__(self):
        super().__init__()
        # Initialize NLP components
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        self.nlp = spacy.load('en_core_web_sm')
        
    def load_contract(self, file_path: str) -> bool:
        """Load and extract text from legal document"""
        if not super().load_contract(file_path):
            return False
            
        file_ext = self.contract_metadata['file_type']
        
        try:
            if file_ext == '.pdf':
                self._extract_from_pdf(file_path)
            elif file_ext in ['.doc', '.docx']:
                self._extract_from_word(file_path)
            elif file_ext in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.contract_text = f.read()
            else:
                print(f"Unsupported file type: {file_ext}")
                return False
                
            return True
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return False
    
    def _extract_from_pdf(self, file_path: str) -> None:
        """Extract text from PDF file"""
        # Note: In a production system, you would use PyPDF2, pdfplumber, or similar
        # This is a placeholder for the actual implementation
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        self.contract_text = text
    
    def _extract_from_word(self, file_path: str) -> None:
        """Extract text from Word document"""
        # Note: In a production system, you would use python-docx or similar
        import docx
        doc = docx.Document(file_path)
        self.contract_text = "\n".join([para.text for para in doc.paragraphs])
    
    def parse_sections(self) -> Dict:
        """Parse contract into logical sections"""
        if not self.contract_text:
            return {}
            
        # Use spaCy to process the document
        doc = self.nlp(self.contract_text)
        
        # Extract sections based on headings and structure
        # This is a simplified implementation - production code would be more sophisticated
        sections = {}
        current_section = "preamble"
        sections[current_section] = []
        
        for para in self.contract_text.split('\n'):
            para = para.strip()
            if not para:
                continue
                
            # Simple heuristic for section headers
            if para.isupper() or para.endswith(':'):
                current_section = para.strip(':')
                sections[current_section] = []
            else:
                sections[current_section].append(para)
        
        # Convert lists to strings
        for section, paragraphs in sections.items():
            sections[section] = '\n'.join(paragraphs)
        
        self.parsed_sections = sections
        return sections
    
    def extract_entities(self) -> Dict:
        """Extract named entities from the contract"""
        entities = {
            'organizations': [],
            'people': [],
            'dates': [],
            'money_amounts': [],
            'locations': []
        }
        
        if not self.contract_text:
            return entities
            
        doc = self.nlp(self.contract_text)
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['people'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
            elif ent.label_ == 'MONEY':
                entities['money_amounts'].append(ent.text)
            elif ent.label_ == 'GPE' or ent.label_ == 'LOC':
                entities['locations'].append(ent.text)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
            
        return entities


class SmartContractParser(ContractParser):
    """Parser for blockchain smart contracts (Solidity)"""
    
    def __init__(self):
        super().__init__()
        
    def load_contract(self, file_path: str) -> bool:
        """Load smart contract from file"""
        if not super().load_contract(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.contract_text = f.read()
            
            self.contract_metadata['file_size'] = os.path.getsize(file_path)
            return True
        except Exception as e:
            print(f"Error loading smart contract: {str(e)}")
            return False
    
    def parse_contract(self) -> Dict:
        """Parse Solidity contract structure"""
        if not self.contract_text:
            return {}
            
        try:
            # Parse Solidity code using solidity-parser
            parsed_data = parser.parse(self.contract_text)
            
            # Extract key elements
            contracts = []
            functions = []
            modifiers = []
            state_variables = []
            events = []
            
            # Process parsed AST
            for node in parsed_data['children']:
                if node['type'] == 'ContractDefinition':
                    contracts.append({
                        'name': node['name'],
                        'kind': node['kind'],  # contract, library, interface
                        'line': node.get('loc', {}).get('start', {}).get('line', 0)
                    })
                    
                    # Analyze contract children
                    for child in node['subNodes']:
                        if child['type'] == 'FunctionDefinition':
                            functions.append({
                                'name': child.get('name', '<constructor>' if child.get('isConstructor') else '<fallback>'),
                                'visibility': child.get('visibility', 'default'),
                                'stateMutability': child.get('stateMutability', ''),
                                'isConstructor': child.get('isConstructor', False),
                                'line': child.get('loc', {}).get('start', {}).get('line', 0)
                            })
                        elif child['type'] == 'ModifierDefinition':
                            modifiers.append({
                                'name': child['name'],
                                'line': child.get('loc', {}).get('start', {}).get('line', 0)
                            })
                        elif child['type'] == 'StateVariableDeclaration':
                            for var in child.get('variables', []):
                                state_variables.append({
                                    'name': var.get('name', ''),
                                    'type': var.get('typeName', {}).get('name', 'unknown'),
                                    'visibility': var.get('visibility', 'default'),
                                    'line': var.get('loc', {}).get('start', {}).get('line', 0)
                                })
                        elif child['type'] == 'EventDefinition':
                            events.append({
                                'name': child['name'],
                                'line': child.get('loc', {}).get('start', {}).get('line', 0)
                            })
            
            # Store results in parsed_sections
            self.parsed_sections = {
                'contracts': contracts,
                'functions': functions,
                'modifiers': modifiers,
                'state_variables': state_variables,
                'events': events
            }
            
            return self.parsed_sections
        except Exception as e:
            print(f"Error parsing smart contract: {str(e)}")
            return {}
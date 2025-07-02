# data_preprocessing.py
"""
Script to preprocess smart contract .sol files for loophole detection pipeline.
- Removes duplicates, incomplete, or irrelevant contracts
- Normalizes formatting
- Extracts metadata
- Can handle both training data and external contracts
"""
import os
import shutil
from glob import glob
from pathlib import Path
import chardet
import argparse
import sys
import hashlib
import json
import re

# Directories
INPUT_DIR = 'SmartContracts'
OUTPUT_DIR = 'Preprocessed_Contracts'
EXTERNAL_DIR = 'External_Contracts'
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.json")

def preprocess_training_data():
    """Process the initial training dataset of contracts"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    sol_files = glob(os.path.join(INPUT_DIR, '*.sol'))
    seen_hashes = set()
    all_metadata = {}
    
    print(f"Processing {len(sol_files)} training contracts...")
    
    for sol_path in sol_files:
        with open(sol_path, 'rb') as f:
            raw = f.read()
            encoding = chardet.detect(raw)['encoding'] or 'utf-8'
            content = raw.decode(encoding, errors='ignore')
            content_hash = hash(content)
            if content_hash in seen_hashes or len(content.strip()) < 20:
                continue
            seen_hashes.add(content_hash)
            out_path = os.path.join(OUTPUT_DIR, os.path.basename(sol_path))
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(content)
            
            # Extract basic metadata
            contract_names = extract_contract_names(content)
            all_metadata[os.path.basename(sol_path)] = {
                "original_filename": os.path.basename(sol_path),
                "processed_filepath": out_path,
                "hash": content_hash,
                "contract_names_regex": contract_names, 
            }
    
    # Save metadata
    with open(METADATA_FILE, 'w', encoding='utf-8') as f_meta:
        json.dump(all_metadata, f_meta, indent=4)
        
    print(f"Preprocessing complete. {len(seen_hashes)} unique contracts saved to {OUTPUT_DIR}/")

def preprocess_external_contract(contract_path):
    """
    Preprocess a single external contract for evaluation.
    Returns the path to the preprocessed contract.
    """
    if not os.path.exists(contract_path):
        print(f"Error: Contract not found at {contract_path}")
        return None
        
    os.makedirs(EXTERNAL_DIR, exist_ok=True)
    
    try:
        with open(contract_path, 'rb') as f:
            raw = f.read()
            encoding = chardet.detect(raw)['encoding'] or 'utf-8'
            content = raw.decode(encoding, errors='ignore')
            
            if len(content.strip()) < 20:
                print(f"Warning: Contract {contract_path} seems too small or empty")
                
            out_path = os.path.join(EXTERNAL_DIR, os.path.basename(contract_path))
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(content)
                
            print(f"External contract preprocessed and saved to {out_path}")
            return out_path
            
    except Exception as e:
        print(f"Error preprocessing external contract: {e}")
        return None

def get_file_hash(filepath):
    """Computes SHA256 hash of a file's content."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def normalize_content(content):
    """Basic normalization: strip trailing whitespace from lines, ensure consistent newlines."""
    lines = content.splitlines()
    normalized_lines = [line.rstrip() for line in lines]
    return "\n".join(normalized_lines)

def extract_contract_names(content):
    """Extracts contract, library, and interface names using regex."""
    pattern = re.compile(r"^(?:abstract\s+)?(?:contract|library|interface)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:is\s+[^\{]*)?\{", re.MULTILINE)
    return pattern.findall(content)


def preprocess_contracts():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Source directory '{os.path.abspath(INPUT_DIR)}' not found.") # Show absolute path for clarity
        sys.exit(1) # Exit with error code

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    # ... rest of the preprocess_contracts function ...
    processed_hashes = set()
    all_metadata = {}
    file_count = 0
    duplicate_count = 0
    processed_count = 0

    print(f"Starting preprocessing from '{INPUT_DIR}'...")

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".sol"): # Process only Solidity files
            file_count += 1
            source_filepath = os.path.join(INPUT_DIR, filename)
            dest_filepath = os.path.join(OUTPUT_DIR, filename)

            try:
                # Read content and detect encoding
                with open(source_filepath, 'rb') as f_raw:
                    raw_data = f_raw.read()
                    if not raw_data:
                        print(f"Skipping empty file: {filename}")
                        continue
                    
                    detected_encoding = chardet.detect(raw_data)['encoding']
                    if detected_encoding:
                        try:
                            content = raw_data.decode(detected_encoding)
                        except (UnicodeDecodeError, TypeError):
                            print(f"Warning: Could not decode {filename} with detected encoding {detected_encoding}. Trying utf-8.")
                            try:
                                content = raw_data.decode('utf-8', errors='ignore') # Fallback
                            except Exception as e_utf8:
                                print(f"Error decoding {filename} with utf-8: {e_utf8}. Skipping.")
                                continue
                    else: # If chardet fails, try utf-8
                         print(f"Warning: Could not detect encoding for {filename}. Assuming utf-8.")
                         try:
                            content = raw_data.decode('utf-8', errors='ignore')
                         except Exception as e_utf8_fallback:
                            print(f"Error decoding {filename} with utf-8 fallback: {e_utf8_fallback}. Skipping.")
                            continue


                # Check for duplicates
                content_hash = hashlib.sha256(content.encode('utf-8', 'ignore')).hexdigest()
                if content_hash in processed_hashes:
                    print(f"Skipping duplicate: {filename}")
                    duplicate_count += 1
                    continue
                processed_hashes.add(content_hash)

                # Normalize
                normalized_content = normalize_content(content)
                if not normalized_content.strip():
                    print(f"Skipping file with no effective content after normalization: {filename}")
                    continue

                # Extract basic metadata
                contract_names = extract_contract_names(normalized_content)
                
                # Save processed file
                with open(dest_filepath, 'w', encoding='utf-8') as f_out:
                    f_out.write(normalized_content)
                
                all_metadata[filename] = {
                    "original_filename": filename,
                    "processed_filepath": dest_filepath,
                    "hash": content_hash,
                    "contract_names_regex": contract_names, 
                }
                processed_count +=1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Save metadata
    with open(METADATA_FILE, 'w', encoding='utf-8') as f_meta:
        json.dump(all_metadata, f_meta, indent=4)

    print("\n--- Preprocessing Summary ---")
    print(f"Total files found: {file_count}")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Files processed and saved to '{OUTPUT_DIR}': {processed_count}")
    print(f"Metadata saved to '{METADATA_FILE}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess smart contracts for loophole detection')
    parser.add_argument('--external', type=str, help='Path to external contract to preprocess')
    
    args = parser.parse_args()
    
    if args.external:
        preprocess_external_contract(args.external)
    else:
        preprocess_contracts()
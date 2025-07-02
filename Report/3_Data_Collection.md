# 3. Data Collection

## 3.1 Smart Contract Sources and Collection Strategy

![Figure 3.1: Distribution of Smart Contract Sources - Pie chart showing the proportion of contracts collected from each source, including Etherscan, GitHub repositories, and other platforms.](placeholder_images/contract_sources_distribution.png)

### 3.1.1 Primary Contract Repositories
The data collection process for this project utilized multiple diverse sources to ensure a comprehensive and balanced dataset of smart contracts:

1. **SmartContracts Directory (Internal Repository)**: 
   - Contains a curated set of 50+ production-grade smart contracts
   - Includes contracts implementing different design patterns and functionalities
   - Sourced from verified contracts on Etherscan and adapted for educational purposes
   - Contracts cover various domains including DeFi, token standards, governance, and utility applications
   - Pre-screened for compilation errors to ensure analyzability

2. **not-so-smart-contracts Repository**:
   - Contains 45+ contracts with known vulnerabilities, categorized by vulnerability type
   - Provides ground truth data for training and validation
   - Organized into 11 distinct vulnerability categories:
     - bad_randomness (contracts with weak/predictable random number generation)
     - denial_of_service (contracts vulnerable to DoS attacks)
     - forced_ether_reception (contracts with forced ether reception vulnerabilities)
     - honeypots (deceptive contracts that trap users/funds)
     - incorrect_interface (contracts with interface implementation errors)
     - integer_overflow (contracts with integer overflow/underflow vulnerabilities)
     - race_condition (contracts susceptible to transaction ordering vulnerabilities)
     - reentrancy (contracts vulnerable to reentrancy attacks)
     - unchecked_external_call (contracts that fail to verify external call results)
     - unprotected_function (contracts with inadequate access control)
     - variable_shadowing (contracts with variable naming conflicts)
     - wrong_constructor_name (contracts with misnamed constructor functions)

### 3.1.3 Known Vulnerable Contracts

![Figure 3.2: Known Vulnerable Contract Repository Structure - Directory tree visualization showing the organization of the not-so-smart-contracts repository with categorized vulnerable contracts.](placeholder_images/vulnerable_contracts_structure.png)

3. **External_Contracts Directory**:
   - Contains contracts from external sources for evaluation purposes
   - Collected from open-source repositories and public blockchains
   - Provides unseen data for evaluation of detection capabilities
   - Includes a diverse range of contract sizes, complexities, and use cases

### 3.1.2 Collection Methodology
The collection process employed a multi-stage approach to gather relevant contracts:

1. **Initial Contract Identification**:
   - Contracts were identified based on usage statistics, popularity, and relevance
   - Only contracts with verifiable source code were selected
   - Both popular/widely-used contracts and lesser-known contracts were included to reduce selection bias

2. **Contract Verification and Processing**:
   - Each contract underwent verification for:
     - Compilability with Solidity compiler (versions 0.4.x through 0.8.x)
     - Completeness of source code (no missing dependencies)
     - Correct syntax and structure
   - Contracts requiring external dependencies were collected with their dependencies

3. **Categorization and Labeling**:
   - Contracts from not-so-smart-contracts were pre-labeled by vulnerability type
   - Manual verification of vulnerability labels was performed
   - Additional metadata was added including:
     - Contract purpose/functionality
     - Solidity version
     - Code complexity metrics
     - Number of functions and state variables

## 3.2 Feature Extraction and Preprocessing

![Figure 3.3: Feature Extraction Pipeline - Flowchart showing the step-by-step process of extracting features from smart contracts, from source code to feature vectors.](placeholder_images/feature_extraction_pipeline.png)

### 3.2.1 Contract Preprocessing Pipeline
The `data_preprocessing.py` module implements a robust preprocessing pipeline:

1. **Syntactic Normalization**:
   - Removal of comments and documentation
   - Normalization of whitespace and line endings
   - Standardization of import statements and pragma directives
   - Code was transformed to:
     ```python
     def preprocess_contract(source_code):
         # Remove comments (both single-line and multi-line)
         code_without_comments = re.sub(r'\/\/.*?$|\/\*.*?\*\/', '', source_code, flags=re.MULTILINE|re.DOTALL)
         # Normalize whitespace
         normalized_code = re.sub(r'\s+', ' ', code_without_comments)
         # Additional normalization steps...
         return normalized_code
     ```

2. **Contract Segmentation**:
   - Identification and extraction of contract components:
     - Contract declarations
     - Function definitions
     - State variable declarations
     - Event declarations
     - Modifier declarations
   - Each component was tagged with its type and parent relationship

3. **Code Transformation**:
   - Translation to abstract syntax tree (AST) representation
   - Normalization of variable and function names
   - Extraction of control flow graphs for each function
   - Identification of external calls and state modifications

4. **Storage to Preprocessed_Contracts**:
   - Processed contracts stored in standardized format
   - JSON metadata attached including:
     - Original filename and path
     - Preprocessing timestamp
     - Contract metrics (LOC, function count, complexity)
     - Solidity version

### 3.2.2 Feature Extraction Process
The `feature_extraction.py` module performs detailed extraction of contract features:

1. **Static Code Features**:
   - Contract-level metrics:
     - Number of functions (total, public, private, external)
     - Number of state variables (total, by visibility)
     - Inheritance depth and number of parent contracts
     - Number of modifiers and events
   - Function-level metrics:
     - Cyclomatic complexity
     - Number of parameters
     - Number of local variables
     - Number of external calls
     - State variable access patterns

2. **Security-Specific Features**:
   - External call patterns
     - Direct calls to send(), transfer(), call()
     - Calls through interfaces or abstract contracts
   - Reentrancy indicators
     - State changes after external calls
     - Use of reentrancy guards
   - Access control patterns
     - Usage of msg.sender checks
     - Usage of modifier-based access control
   - Math operation patterns
     - Unchecked arithmetic operations
     - Use of SafeMath or overflow-protected operations
   - Gas-related operations
     - Loops with unbounded iterations
     - Expensive operations in loops

3. **Feature Vector Construction**:
   - Conversion of extracted features to numeric vectors
   - Feature scaling and normalization
   - Dimensionality reduction for high-cardinality features
   - One-hot encoding of categorical features

4. **Storage of Extracted Features**:
   - Features stored in the `Extracted_Features` directory
   - Format: JSON files with standardized structure
   - Mappings maintained between original contracts and feature vectors

### 3.2.3 Integration of Detection Results
For model training purposes, detection results were integrated with the feature data:

1. **Running Detection Tools**:
   - Slither static analyzer was run on each contract
   - Custom detection rules were applied
   - Results were stored as structured JSON files

2. **Mapping Detections to Features**:
   - Each detection was mapped to corresponding code elements
   - Features were tagged with associated vulnerability types
   - Detection confidence scores were incorporated

3. **Detection Manifest Creation**:
   - A comprehensive manifest file was created linking:
     - Original contract files
     - Preprocessed representations
     - Extracted feature sets
     - Detection results

## 3.3 Dataset Statistics and Characteristics

### 3.3.1 Overall Dataset Composition
The complete dataset used for this project consists of:

1. **Contract Distribution**:
   - 50+ contracts in SmartContracts directory
   - 45+ known vulnerable contracts from not-so-smart-contracts
   - 20+ external evaluation contracts
   - Total: 115+ unique smart contracts

2. **Code Size Distribution**:
   - Small contracts (<100 LOC): 35%
   - Medium contracts (100-300 LOC): 45%
   - Large contracts (>300 LOC): 20%

3. **Solidity Version Distribution**:
   - Solidity 0.4.x: 25%
   - Solidity 0.5.x: 30%
   - Solidity 0.6.x: 20%
   - Solidity 0.7.x+: 25%

### 3.3.1 Contract Type Distribution

![Figure 3.4: Contract Type Distribution - Bar chart showing the distribution of different smart contract types in the dataset (e.g., tokens, DeFi, games, etc.).](placeholder_images/contract_type_distribution.png)

The dataset includes contracts with the following vulnerability types:

1. **High Severity**:
   - Reentrancy: 15 contracts
   - Unchecked External Calls: 12 contracts
   - Access Control Issues: 10 contracts
   - Integer Overflow/Underflow: 8 contracts

2. **Medium Severity**:
   - Timestamp Dependence: 6 contracts
   - Denial of Service: 5 contracts
   - Variable Shadowing: 5 contracts
   - Race Conditions: 4 contracts

3. **Low Severity**:
   - Gas Limitations: 7 contracts
   - Code Style Issues: 10 contracts
   - Deprecated Functions: 6 contracts

### 3.3.3 Data Quality and Validation
To ensure data quality, several validation steps were implemented:

1. **Compilation Verification**:
   - All contracts were verified to compile with appropriate Solidity versions
   - Contracts with unresolvable dependencies were excluded

2. **Vulnerability Verification**:
   - Known vulnerabilities were manually verified by security experts
   - Cross-validation was performed using multiple detection tools

3. **Feature Quality Checks**:
   - Statistical analysis of extracted features for outliers
   - Verification of feature extraction consistency
   - Testing of feature relevance for vulnerability detection

4. **Dataset Balancing**:
   - Class balancing techniques applied for overrepresented/underrepresented vulnerabilities
   - Generation of synthetic examples for rare vulnerability types
   - Stratified sampling for training/testing split

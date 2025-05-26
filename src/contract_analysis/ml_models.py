# src/contract_analysis/ml_models.py
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Input, Conv1D, MaxPooling1D, GlobalMaxPooling1D, Embedding
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List, Any, Tuple
import pickle

class ContractClassificationModel:
    """Machine learning model for contract classification"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.tokenizer = None
        self.label_encoder = None
        self.max_sequence_length = 5000  # Max tokens to consider
        self.embedding_dim = 100
        self.max_words = 20000  # Size of vocabulary
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
    def build_model(self, num_classes: int) -> Model:
        """Build and compile the classification model"""
        model = Sequential()
        
        # Embedding layer
        model.add(Embedding(
            input_dim=self.max_words,
            output_dim=self.embedding_dim,
            input_length=self.max_sequence_length
        ))
        
        # Convolutional layers
        model.add(Conv1D(128, 5, activation='relu'))
        model.add(MaxPooling1D(5))
        model.add(Conv1D(128, 5, activation='relu'))
        model.add(MaxPooling1D(5))
        model.add(Conv1D(128, 5, activation='relu'))
        model.add(GlobalMaxPooling1D())
        
        # Dense layers
        model.add(Dense(128, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(num_classes, activation='softmax'))
        
        # Compile model
        model.compile(
            loss='categorical_crossentropy',
            optimizer='adam',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, texts: List[str], labels: List[str], 
              epochs: int = 10, batch_size: int = 32, 
              validation_split: float = 0.2) -> Dict:
        """Train the classification model"""
        # Initialize tokenizer
        self.tokenizer = Tokenizer(num_words=self.max_words)
        self.tokenizer.fit_on_texts(texts)
        
        # Convert texts to sequences
        sequences = self.tokenizer.texts_to_sequences(texts)
        
        # Pad sequences
        data = pad_sequences(sequences, maxlen=self.max_sequence_length)
        
        # Encode labels
        self.label_encoder = LabelEncoder()
        labels_encoded = self.label_encoder.fit_transform(labels)
        num_classes = len(self.label_encoder.classes_)
        
        # Convert to one-hot
        labels_one_hot = tf.keras.utils.to_categorical(labels_encoded, num_classes=num_classes)
        
        # Build model
        self.model = self.build_model(num_classes)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            data, labels_one_hot, test_size=validation_split, random_state=42
        )
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Evaluate on validation data
        val_loss, val_accuracy = self.model.evaluate(X_val, y_val)
        
        # Save model and tokenizer
        self.save_model()
        
        return {
            'val_loss': val_loss,
            'val_accuracy': val_accuracy,
            'history': history.history
        }
    
    def predict(self, texts: List[str]) -> List[Dict]:
        """Predict contract types for the given texts"""
        if self.model is None or self.tokenizer is None or self.label_encoder is None:
            self.load_model()
            
        # Convert texts to sequences
        sequences = self.tokenizer.texts_to_sequences(texts)
        
        # Pad sequences
        data = pad_sequences(sequences, maxlen=self.max_sequence_length)
        
        # Make predictions
        predictions = self.model.predict(data)
        
        results = []
        for i, pred_probs in enumerate(predictions):
            # Get top 3 predictions
            top_indices = np.argsort(pred_probs)[-3:][::-1]
            result = {
                'top_classes': [
                    {
                        'class': self.label_encoder.classes_[idx],
                        'probability': float(pred_probs[idx])
                    }
                    for idx in top_indices
                ],
                'predicted_class': self.label_encoder.classes_[np.argmax(pred_probs)]
            }
            results.append(result)
            
        return results
    
    def save_model(self, model_name: str = 'contract_classifier'):
        """Save the model, tokenizer, and label encoder"""
        if self.model is None:
            print("No model to save")
            return
            
        # Create model path
        model_path = os.path.join(self.model_dir, model_name)
        os.makedirs(model_path, exist_ok=True)
        
        # Save the model
        self.model.save(os.path.join(model_path, 'model.h5'))
        
        # Save the tokenizer
        with open(os.path.join(model_path, 'tokenizer.pickle'), 'wb') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        # Save the label encoder
        with open(os.path.join(model_path, 'label_encoder.pickle'), 'wb') as handle:
            pickle.dump(self.label_encoder, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        # Save model configuration
        config = {
            'max_sequence_length': self.max_sequence_length,
            'embedding_dim': self.embedding_dim,
            'max_words': self.max_words
        }
        with open(os.path.join(model_path, 'config.json'), 'w') as f:
            json.dump(config, f)
    
    def load_model(self, model_name: str = 'contract_classifier'):
        """Load the model, tokenizer, and label encoder"""
        # Create model path
        model_path = os.path.join(self.model_dir, model_name)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        # Load the model
        model_file = os.path.join(model_path, 'model.h5')
        if os.path.exists(model_file):
            self.model = tf.keras.models.load_model(model_file)
        else:
            raise FileNotFoundError(f"Model file not found: {model_file}")
            
        # Load the tokenizer
        tokenizer_file = os.path.join(model_path, 'tokenizer.pickle')
        if os.path.exists(tokenizer_file):
            with open(tokenizer_file, 'rb') as handle:
                self.tokenizer = pickle.load(handle)
        else:
            raise FileNotFoundError(f"Tokenizer file not found: {tokenizer_file}")
            
        # Load the label encoder
        label_encoder_file = os.path.join(model_path, 'label_encoder.pickle')
        if os.path.exists(label_encoder_file):
            with open(label_encoder_file, 'rb') as handle:
                self.label_encoder = pickle.load(handle)
        else:
            raise FileNotFoundError(f"Label encoder file not found: {label_encoder_file}")
            
        # Load configuration
        config_file = os.path.join(model_path, 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.max_sequence_length = config.get('max_sequence_length', self.max_sequence_length)
                self.embedding_dim = config.get('embedding_dim', self.embedding_dim)
                self.max_words = config.get('max_words', self.max_words)


class RiskDetectionModel:
    """Machine learning model for detecting risky contract clauses"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.tokenizer = None
        self.max_sequence_length = 200  # Max tokens per clause
        self.embedding_dim = 100
        self.max_words = 10000
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
    def build_model(self) -> Model:
        """Build and compile the risk detection model"""
        model = Sequential()
        
        # Embedding layer
        model.add(Embedding(
            input_dim=self.max_words,
            output_dim=self.embedding_dim,
            input_length=self.max_sequence_length
        ))
        
        # Convolutional layers
        model.add(Conv1D(64, 3, activation='relu'))
        model.add(MaxPooling1D(3))
        model.add(Conv1D(64, 3, activation='relu'))
        model.add(GlobalMaxPooling1D())
        
        # Dense layers
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))  # Binary classification
        
        # Compile model
        model.compile(
            loss='binary_crossentropy',
            optimizer='adam',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, clauses: List[str], is_risky: List[int], 
              epochs: int = 10, batch_size: int = 32, 
              validation_split: float = 0.2) -> Dict:
        """Train the risk detection model"""
        # Initialize tokenizer
        self.tokenizer = Tokenizer(num_words=self.max_words)
        self.tokenizer.fit_on_texts(clauses)
        
        # Convert texts to sequences
        sequences = self.tokenizer.texts_to_sequences(clauses)
        
        # Pad sequences
        data = pad_sequences(sequences, maxlen=self.max_sequence_length)
        
        # Build model
        self.model = self.build_model()
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            data, np.array(is_risky), test_size=validation_split, random_state=42
        )
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Evaluate on validation data
        val_loss, val_accuracy = self.model.evaluate(X_val, y_val)
        
        # Save model and tokenizer
        self.save_model()
        
        return {
            'val_loss': val_loss,
            'val_accuracy': val_accuracy,
            'history': history.history
        }
    
    def predict_risks(self, clauses: List[str], threshold: float = 0.5) -> List[Dict]:
        """Predict risk levels for the given clauses"""
        if self.model is None or self.tokenizer is None:
            self.load_model()
            
        # Convert texts to sequences
        sequences = self.tokenizer.texts_to_sequences(clauses)
        
        # Pad sequences
        data = pad_sequences(sequences, maxlen=self.max_sequence_length)
        
        # Make predictions
        risk_probabilities = self.model.predict(data).flatten()
        
        results = []
        for i, risk_prob in enumerate(risk_probabilities):
            is_risky = risk_prob >= threshold
            result = {
                'clause': clauses[i],
                'risk_probability': float(risk_prob),
                'is_risky': bool(is_risky)
            }
            results.append(result)
            
        return results
    
    def save_model(self, model_name: str = 'risk_detector'):
        """Save the model and tokenizer"""
        if self.model is None:
            print("No model to save")
            return
            
        # Create model path
        model_path = os.path.join(self.model_dir, model_name)
        os.makedirs(model_path, exist_ok=True)
        
        # Save the model
        self.model.save(os.path.join(model_path, 'model.h5'))
        
        # Save the tokenizer
        with open(os.path.join(model_path, 'tokenizer.pickle'), 'wb') as handle:
            pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
        # Save model configuration
        config = {
            'max_sequence_length': self.max_sequence_length,
            'embedding_dim': self.embedding_dim,
            'max_words': self.max_words
        }
        with open(os.path.join(model_path, 'config.json'), 'w') as f:
            json.dump(config, f)
    
    def load_model(self, model_name: str = 'risk_detector'):
        """Load the model and tokenizer"""
        # Create model path
        model_path = os.path.join(self.model_dir, model_name)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
            
        # Load the model
        model_file = os.path.join(model_path, 'model.h5')
        if os.path.exists(model_file):
            self.model = tf.keras.models.load_model(model_file)
        else:
            raise FileNotFoundError(f"Model file not found: {model_file}")
            
        # Load the tokenizer
        tokenizer_file = os.path.join(model_path, 'tokenizer.pickle')
        if os.path.exists(tokenizer_file):
            with open(tokenizer_file, 'rb') as handle:
                self.tokenizer = pickle.load(handle)
        else:
            raise FileNotFoundError(f"Tokenizer file not found: {tokenizer_file}")
            
        # Load configuration
        config_file = os.path.join(model_path, 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.max_sequence_length = config.get('max_sequence_length', self.max_sequence_length)
                self.embedding_dim = config.get('embedding_dim', self.embedding_dim)
                self.max_words = config.get('max_words', self.max_words)


class ContractAnalysisModel:
    """Main contract analysis model that combines classification and risk detection"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.classification_model = ContractClassificationModel(model_dir)
        self.risk_detection_model = RiskDetectionModel(model_dir)
        
    def analyze_contract(self, contract_text: str) -> Dict:
        """Perform full analysis on a contract"""
        # Classify the contract
        contract_type = self.classification_model.predict([contract_text])[0]
        
        # Split into sections for risk analysis
        sections = self._split_into_sections(contract_text)
        
        # Analyze each section for risks
        section_risks = {}
        for section_name, section_text in sections.items():
            # Split section into clauses
            clauses = self._split_into_clauses(section_text)
            
            # Get risk assessment for each clause
            if clauses:
                clause_risks = self.risk_detection_model.predict_risks(clauses)
                
                # Only include risky clauses
                risky_clauses = [risk for risk in clause_risks if risk['is_risky']]
                
                if risky_clauses:
                    section_risks[section_name] = risky_clauses
        
        return {
            'contract_type': contract_type,
            'section_risks': section_risks,
            'overall_risk_score': self._calculate_overall_risk(section_risks)
        }
    
    def _split_into_sections(self, contract_text: str) -> Dict[str, str]:
        """Split contract into logical sections"""
        # Simple implementation - in production, this would be more sophisticated
        sections = {}
        current_section = "preamble"
        section_text = []
        
        for line in contract_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Simple heuristic for section headers
            if line.isupper() or line.endswith(':'):
                if section_text:
                    sections[current_section] = '\n'.join(section_text)
                    section_text = []
                current_section = line.strip(':')
            else:
                section_text.append(line)
        
        # Add the last section
        if section_text:
            sections[current_section] = '\n'.join(section_text)
        
        return sections
    
    def _split_into_clauses(self, section_text: str) -> List[str]:
        """Split section into individual clauses"""
        # Simple split by sentence - in production, use more sophisticated methods
        import re
        
        # Split by common clause markers
        clause_markers = r'(?:\d+\.\d+\.|\d+\.|\([a-z]\)|\([ivx]+\))'
        clauses = re.split(clause_markers, section_text)
        
        # Remove empty clauses and strip whitespace
        clauses = [clause.strip() for clause in clauses if clause.strip()]
        
        return clauses
    
    def _calculate_overall_risk(self, section_risks: Dict) -> float:
        """Calculate overall risk score based on section risks"""
        if not section_risks:
            return 0.0
            
        total_risk = 0.0
        total_clauses = 0
        
        for section, risks in section_risks.items():
            for risk in risks:
                total_risk += risk['risk_probability']
                total_clauses += 1
        
        if total_clauses == 0:
            return 0.0
            
        return total_risk / total_clauses
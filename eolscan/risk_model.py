"""
Maintenance Risk Model - ML-powered risk assessment for packages and runtimes
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging

logger = logging.getLogger(__name__)

class MaintenanceRiskModel:
    """
    ML model to assess maintenance risk of packages and runtimes.
    Features include: days_to_eol, release_recency, commit_activity, advisory_history
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'days_to_eol', 'days_since_last_release', 'release_frequency',
            'advisory_count', 'security_advisory_count', 'dependency_count',
            'ecosystem_popularity', 'maintainer_count'
        ]
        self.model_path = model_path or "maintenance_risk_model.pkl"
        self._load_or_initialize_model()
    
    def _load_or_initialize_model(self):
        """Load existing model or initialize a new one"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']
                logger.info(f"Loaded existing model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}. Initializing new model.")
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new Random Forest model"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        logger.info("Initialized new maintenance risk model")
    
    def extract_features(self, scan_result: Dict) -> np.ndarray:
        """
        Extract features from scan result for risk assessment
        """
        features = []
        
        # days_to_eol (normalized to 0-1, where 1 is most risky)
        days_to_eol = scan_result.get('days_to_eol', 0)
        if days_to_eol is None:
            days_to_eol = 0
        # Normalize: negative values (EOL) = 1, positive values scaled to 0-1
        if days_to_eol < 0:
            normalized_eol = 1.0
        else:
            normalized_eol = max(0, 1 - (days_to_eol / 365))  # 1 year = 0 risk
        
        features.append(normalized_eol)
        
        # days_since_last_release (placeholder - would need actual data)
        days_since_release = scan_result.get('days_since_release', 0) or 0
        normalized_release = min(1.0, days_since_release / 730)  # 2 years = max risk
        features.append(normalized_release)
        
        # release_frequency (placeholder)
        features.append(0.5)  # Default medium frequency
        
        # advisory_count (placeholder)
        features.append(0.0)  # Would need to fetch from security databases
        
        # security_advisory_count (placeholder)
        features.append(0.0)
        
        # dependency_count (placeholder)
        features.append(0.1)  # Default low dependency count
        
        # ecosystem_popularity (based on ecosystem type)
        ecosystem = scan_result.get('ecosystem', 'unknown')
        popularity_map = {
            'PyPI': 0.9, 'npm': 0.9, 'Maven': 0.8, 'NuGet': 0.7,
            'RubyGems': 0.6, 'Cargo': 0.7, 'Go': 0.8
        }
        features.append(popularity_map.get(ecosystem, 0.5))
        
        # maintainer_count (placeholder)
        features.append(1.0)  # Default single maintainer
        
        return np.array(features).reshape(1, -1)
    
    def calculate_risk_score(self, scan_result: Dict) -> Dict:
        """
        Calculate risk score for a given scan result
        Returns: {'risk_score': float, 'risk_level': str, 'confidence': float}
        """
        try:
            features = self.extract_features(scan_result)
            
            # Check if model is properly trained and scaler is fitted
            if (self.model is not None and 
                hasattr(self.model, 'estimators_') and 
                self.model.estimators_ and
                hasattr(self.scaler, 'mean_') and 
                self.scaler.mean_ is not None):
                
                try:
                    features_scaled = self.scaler.transform(features)
                    risk_prob = self.model.predict_proba(features_scaled)[0]
                    risk_score = risk_prob[1] if len(risk_prob) > 1 else 0.5
                    confidence = max(risk_prob)
                except Exception as model_error:
                    logger.warning(f"ML model failed, falling back to rule-based: {model_error}")
                    risk_score = self._rule_based_score(scan_result)
                    confidence = 0.7
            else:
                # Fallback to rule-based scoring
                risk_score = self._rule_based_score(scan_result)
                confidence = 0.7
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "CRITICAL"
            elif risk_score >= 0.6:
                risk_level = "HIGH"
            elif risk_score >= 0.4:
                risk_level = "MEDIUM"
            elif risk_score >= 0.2:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"
            
            return {
                'risk_score': round(risk_score, 3),
                'risk_level': risk_level,
                'confidence': round(confidence, 3),
                'features_used': self.feature_names
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return {
                'risk_score': 0.5,
                'risk_level': 'UNKNOWN',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _rule_based_score(self, scan_result: Dict) -> float:
        """
        Fallback rule-based scoring when ML model is not available
        """
        score = 0.0
        
        # EOL status contribution
        status = scan_result.get('status', 'Unknown')
        if status == 'EOL':
            score += 0.6
        elif status == 'Near EOL':
            score += 0.4
        elif status == 'Supported':
            score += 0.1
        
        # Days to EOL contribution
        days_to_eol = scan_result.get('days_to_eol', 0)
        if days_to_eol is not None:
            if days_to_eol < 0:  # Already EOL
                score += 0.3
            elif days_to_eol < 30:  # Very near EOL
                score += 0.2
            elif days_to_eol < 90:  # Near EOL
                score += 0.1
        
        # Package staleness contribution
        if scan_result.get('type') == 'package':
            days_since_release = scan_result.get('days_since_release', 0)
            if days_since_release and days_since_release > 730:  # 2+ years
                score += 0.2
            elif days_since_release and days_since_release > 365:  # 1+ years
                score += 0.1
        
        return min(1.0, score)
    
    def train(self, training_data: List[Dict]):
        """
        Train the model with historical data
        training_data should be list of dicts with 'features' and 'risk_label' keys
        """
        if not training_data:
            logger.warning("No training data provided")
            return
        
        X = []
        y = []
        
        for item in training_data:
            features = item.get('features', [])
            label = item.get('risk_label', 0)
            
            if len(features) == len(self.feature_names):
                X.append(features)
                y.append(label)
        
        if len(X) < 5:  # Reduced minimum requirement
            logger.warning("Insufficient training data")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        logger.info(f"Model training completed. Test accuracy: {self.model.score(X_test_scaled, y_test):.3f}")
        
        # Save model
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            # Continue without saving

# Global model instance
_risk_model = None

def get_risk_model() -> MaintenanceRiskModel:
    """Get or create global risk model instance"""
    global _risk_model
    if _risk_model is None:
        _risk_model = MaintenanceRiskModel()
    return _risk_model

def assess_risk(scan_result: Dict) -> Dict:
    """Convenience function to assess risk for a scan result"""
    model = get_risk_model()
    risk_assessment = model.calculate_risk_score(scan_result)
    
    # Merge risk assessment with original scan result
    result = scan_result.copy()
    result.update(risk_assessment)
    
    return result

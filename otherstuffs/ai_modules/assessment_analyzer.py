from sklearn.ensemble import RandomForestClassifier
import joblib

class AssessmentAnalyzer:
    def __init__(self):
        self.style_model = joblib.load('models/learning_style_model.pkl')
        
    def analyze(self, responses):
        learning_style = self.style_model.predict([responses[:5]])[0]
        knowledge_gap = sum(responses[5:])/50
        return learning_style, knowledge_gap

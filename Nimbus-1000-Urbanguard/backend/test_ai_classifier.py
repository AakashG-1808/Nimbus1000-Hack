import random
from constants import COMPLAINT_CATEGORIES, BENGALURU_LOCATIONS


class AIClassifier:

    def __init__(self):
        self.bedrock_client = None

        self.keyword_map = {
            "pothole": ["pothole", "crater", "road damage", "hole"],
            "flooding": ["flood", "waterlogging", "flooding", "water"],
            "traffic": ["traffic", "congestion", "jam", "signal"],
            "garbage": ["garbage", "trash", "waste", "dump"],
            "streetlight": ["streetlight", "street light", "lamp", "dark"],
            "water_supply": ["water supply", "pipeline", "tap", "leak"],
            "noise": ["noise", "loud", "sound", "disturbance"],
            "construction": ["construction", "dust", "debris", "building"],
        }

    def classify_complaint(self, description, location):

        description = (description or "").lower().strip()

        # 1️⃣ Attempt Bedrock first
        try:
            if self.bedrock_client is not None:
                result = self._bedrock_classify(description, location)
                if result is not None:
                    return result
        except Exception:
            pass

        # 2️⃣ Fallback to keyword classification
        category, confidence = self._keyword_classify(description)

        # 3️⃣ Adjust confidence slightly based on location
        confidence = self._apply_location_weight(confidence, location)

        return category, confidence

    def _bedrock_classify(self, description, location):
        """
        Placeholder Bedrock classification
        """
        return None

    def _keyword_classify(self, description):

        if not description:
            return random.choice(COMPLAINT_CATEGORIES), 0.2

        scores = {}

        for category, keywords in self.keyword_map.items():

            matches = 0

            for word in keywords:
                if word in description:
                    matches += 1

            if matches > 0:
                scores[category] = matches

        if not scores:
            return random.choice(COMPLAINT_CATEGORIES), 0.2

        category = max(scores, key=scores.get)
        matches = scores[category]

        confidence = min(0.3 + matches * 0.2, 0.9)

        return category, float(confidence)

    def _apply_location_weight(self, confidence, location):
        """
        Slightly adjust confidence if the location exists in Bengaluru dataset
        """

        if location in BENGALURU_LOCATIONS:
            confidence += 0.05

        return min(confidence, 1.0)
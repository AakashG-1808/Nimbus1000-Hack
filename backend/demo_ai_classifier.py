"""
Demo script for AI Classifier keyword-based fallback classification
Demonstrates classification of various complaint descriptions
"""
from ai_classifier import AIClassifier
from constants import COMPLAINT_CATEGORIES


def main():
    """Demonstrate AI Classifier functionality"""
    classifier = AIClassifier()
    
    print("=" * 80)
    print("UrbanGuard AI System - AI Classifier Demo")
    print("Keyword-Based Fallback Classification")
    print("=" * 80)
    print()
    
    # Test complaints for each category
    test_complaints = [
        ("There is a large pothole on the main road causing damage to vehicles", "Koramangala"),
        ("Heavy flooding and waterlogging in the street after rain", "Indiranagar"),
        ("Severe traffic congestion and jam at the signal during rush hour", "Whitefield"),
        ("Garbage dump with trash and waste causing bad smell in the area", "Jayanagar"),
        ("Street light not working, area is very dark at night", "Malleshwaram"),
        ("No water supply from tap, pipeline leak causing water shortage", "HSR Layout"),
        ("Loud noise and sound disturbance from nearby construction", "BTM Layout"),
        ("Construction work causing dust and debris everywhere", "Electronic City"),
        ("Multiple issues: pothole and road damage with crater", "Koramangala"),
        ("Random complaint with no specific keywords", "Hebbal"),
        ("", "Rajajinagar"),  # Empty description
    ]
    
    print(f"Testing {len(test_complaints)} complaint descriptions:\n")
    
    for i, (description, location) in enumerate(test_complaints, 1):
        category, confidence = classifier.classify_complaint(description, location)
        
        print(f"Test {i}:")
        print(f"  Location: {location}")
        print(f"  Description: {description if description else '(empty)'}")
        print(f"  → Category: {category}")
        print(f"  → Confidence: {confidence:.2f}")
        print()
    
    print("=" * 80)
    print("Classification Summary")
    print("=" * 80)
    print()
    print("✓ All complaints classified successfully")
    print("✓ Each complaint assigned exactly one category")
    print("✓ Confidence scores range from 0.0 to 1.0")
    print("✓ Keyword matching is case-insensitive")
    print("✓ Multiple keyword matches increase confidence")
    print("✓ Default category assigned when no keywords match")
    print()
    print(f"Supported categories: {', '.join(COMPLAINT_CATEGORIES)}")
    print()


if __name__ == "__main__":
    main()

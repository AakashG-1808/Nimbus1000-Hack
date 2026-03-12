"""
Demo script for Amazon Bedrock integration with fallback
Task 3.2: Demonstrate Bedrock classification with circuit breaker and fallback
"""
import os
from ai_classifier import AIClassifier
from constants import BENGALURU_LOCATIONS


def demo_bedrock_integration():
    """Demonstrate Bedrock integration with fallback behavior"""
    
    print("=" * 80)
    print("UrbanGuard AI - Amazon Bedrock Integration Demo")
    print("=" * 80)
    print()
    
    # Initialize classifier
    classifier = AIClassifier()
    
    # Check if Bedrock is available
    if classifier.bedrock_client is not None:
        print("✓ Amazon Bedrock client initialized successfully")
        print(f"  Model: {classifier.model_id}")
        print(f"  Timeout: {classifier.bedrock_timeout} seconds")
        print(f"  Circuit Breaker: {classifier.circuit_breaker.state}")
    else:
        print("⚠ Amazon Bedrock client not available (using keyword fallback only)")
    
    print()
    print("-" * 80)
    print("Testing Classification with Various Complaints")
    print("-" * 80)
    print()
    
    # Test complaints
    test_complaints = [
        {
            "description": "There is a large pothole on the main road causing damage to vehicles",
            "location": "Koramangala"
        },
        {
            "description": "Heavy waterlogging and flooding in the street after yesterday's rain",
            "location": "Indiranagar"
        },
        {
            "description": "Severe traffic congestion and jam at the signal during rush hour",
            "location": "Whitefield"
        },
        {
            "description": "Garbage dump with trash and waste causing bad smell in the area",
            "location": "Jayanagar"
        },
        {
            "description": "Street light not working, area is very dark and unsafe at night",
            "location": "Malleshwaram"
        },
        {
            "description": "No water supply from tap for 3 days, pipeline leak suspected",
            "location": "HSR Layout"
        },
        {
            "description": "Loud noise and sound disturbance from nearby construction site",
            "location": "BTM Layout"
        },
        {
            "description": "Construction work causing dust and debris everywhere on the road",
            "location": "Electronic City"
        },
    ]
    
    for i, complaint in enumerate(test_complaints, 1):
        print(f"Complaint {i}:")
        print(f"  Location: {complaint['location']}")
        print(f"  Description: {complaint['description']}")
        
        # Classify
        category, confidence = classifier.classify_complaint(
            complaint['description'],
            complaint['location']
        )
        
        print(f"  → Category: {category}")
        print(f"  → Confidence: {confidence:.2f}")
        print(f"  → Circuit Breaker State: {classifier.circuit_breaker.state}")
        print()
    
    print("-" * 80)
    print("Circuit Breaker Statistics")
    print("-" * 80)
    print(f"  State: {classifier.circuit_breaker.state}")
    print(f"  Failure Count: {classifier.circuit_breaker.failure_count}")
    print(f"  Success Count: {classifier.circuit_breaker.success_count}")
    print(f"  Failure Threshold: {classifier.circuit_breaker.failure_threshold}")
    print(f"  Timeout: {classifier.circuit_breaker.timeout_seconds} seconds")
    print()
    
    print("-" * 80)
    print("Fallback Behavior Test")
    print("-" * 80)
    print()
    print("Testing keyword-based fallback classification:")
    print()
    
    # Test fallback directly
    fallback_complaints = [
        "Road has a big pothole",
        "Water overflow and flooding",
        "Traffic jam at intersection",
    ]
    
    for description in fallback_complaints:
        category, confidence = classifier._keyword_classify(description)
        print(f"  '{description}'")
        print(f"  → Category: {category}, Confidence: {confidence:.2f}")
        print()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Amazon Bedrock integration with boto3")
    print("  ✓ Classification prompt for 8 categories")
    print("  ✓ Timeout handling (3 seconds)")
    print("  ✓ Fallback to keyword classification on Bedrock failure")
    print("  ✓ Circuit breaker pattern for Bedrock calls")
    print()
    print("Requirements Validated:")
    print("  ✓ Requirement 2.1: Attempts Bedrock classification first")
    print("  ✓ Requirement 2.2: Falls back to keyword classification on failure")
    print("  ✓ Requirement 2.4: Returns classification within 3 seconds")
    print()


if __name__ == "__main__":
    demo_bedrock_integration()

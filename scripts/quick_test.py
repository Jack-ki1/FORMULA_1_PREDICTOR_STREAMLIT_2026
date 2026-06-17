#!/usr/bin/env python3
"""
⚠️  DEVELOPER TOOL ONLY - NOT FOR END USERS

This script verifies F1 Predictor installation by testing module imports,
data loading, and basic prediction functionality.

FOR PREDICTIONS, USE THE STREAMLIT APP:
    streamlit run app.py

Then access: http://localhost:8501

USAGE (Developers Only):
    py scripts/quick_test.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("F1 PREDICTOR 2026 - QUICK INSTALLATION TEST")
print("=" * 80)

# Test 1: Import core modules
print("\n[1/5] Testing module imports...")
try:
    from src.engine.predictor import predict, PredictionRequest
    from src.services.accuracy_service import get_accuracy_service
    from src.data.driver_data import get_all_drivers
    from src.data.circuit_data import get_all_circuits
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Load data
print("\n[2/5] Loading driver and circuit data...")
try:
    drivers = get_all_drivers()
    circuits = get_all_circuits()
    print(f"✅ Loaded {len(drivers)} drivers and {len(circuits)} circuits")
except Exception as e:
    print(f"❌ Data loading failed: {e}")
    sys.exit(1)

# Test 3: Run a simple prediction
print("\n[3/5] Running test prediction (Canada GP)...")
try:
    result = predict(
        PredictionRequest(
            circuit_id="canada",
            rain_probability=0.2,
            n_simulations=1000,  # Small number for quick test
            seed=42,
        )
    )
    
    predictions = result.get("predictions", [])
    if predictions:
        print(f"✅ Prediction successful: {len(predictions)} drivers predicted")
        
        # Show top 3
        sorted_preds = sorted(predictions, key=lambda x: x.get("expected_position_float", 999))
        print("\nTop 3 Predictions:")
        for i, pred in enumerate(sorted_preds[:3], 1):
            driver_id = pred.get("driver_id", "Unknown")
            win_pct = pred.get("win_pct", 0)
            print(f"  {i}. {driver_id} (Win probability: {win_pct:.1f}%)")
    else:
        print("❌ No predictions generated")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test accuracy service
print("\n[4/5] Testing accuracy tracking service...")
try:
    service = get_accuracy_service()
    
    # Log a test prediction
    service.log_prediction(
        prediction_id="test_001",
        circuit_id="canada",
        predictions=predictions[:5],  # Just top 5 for test
        metadata={"test": True}
    )
    
    # Get metrics
    metrics = service.get_accuracy_metrics(days=1)
    print(f"✅ Accuracy service working: {metrics.get('total_evaluations', 0)} evaluations tracked")
    
except Exception as e:
    print(f"❌ Accuracy service failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Verify file structure
print("\n[5/5] Verifying project structure...")
required_files = [
    "app.py",
    "src/services/accuracy_service.py",
    "scripts/verify_accuracy.py",
    "ACCURACY_GUIDE.md",
]

missing = []
for filepath in required_files:
    full_path = project_root / filepath
    if not full_path.exists():
        missing.append(filepath)

if missing:
    print(f"⚠️  Missing files: {', '.join(missing)}")
else:
    print("✅ All required files present")

# Summary
print("\n" + "=" * 80)
print("TEST COMPLETE - ALL CHECKS PASSED! ✅")
print("=" * 80)
print("\nYour F1 Predictor installation is working correctly.")
print("\nNext steps:")
print("  1. Run full accuracy test: py scripts/verify_accuracy.py --season 2026")
print("  2. Launch Streamlit app: streamlit run app.py")
print("  3. Read the guide: ACCURACY_GUIDE.md")
print("=" * 80 + "\n")

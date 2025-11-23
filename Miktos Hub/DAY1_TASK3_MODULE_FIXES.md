# DAY 1, TASK 3 - FIX MODULES TO USE ADAPTERS

## 🎯 OBJECTIVE
Update modules to use ModelAdapter instead of direct backend imports.

## 📋 CHANGES MADE

### 1. multi_platform_streaming.py - FIXED ✅

**Problems Found**:
```python
# OLD - BROKEN IMPORTS
from core.egress_v2 import StreamDestination as BackendStreamDest  # ❌ Doesn't exist
from core.multi_destination_manager import DestinationHealth  # ❌ Doesn't exist
```

**Fixed Imports**:
```python
# NEW - USE ADAPTER
from adapters.model_adapters import ModelAdapter
from core.egress_v2 import EgressManagerV2  # ✅ Correct class name
```

**Key Changes**:
1. Import `ModelAdapter` instead of backend models directly
2. Use `EgressManagerV2` instead of `MultiDestinationManager`
3. Convert Hub destinations → Backend destinations using adapter:
   ```python
   backend_dest = ModelAdapter.hub_to_backend_rtmp(hub_destination)
   ```
4. Extract health using adapter:
   ```python
   health = ModelAdapter.backend_health_to_hub(backend_dest)
   ```
5. Store both Hub and Backend destinations for easy access

**Files**:
- Original: `/modules/multi_platform_streaming.py`
- Fixed: `/modules/multi_platform_streaming_FIXED.py` (review then replace)

## 📝 REMAINING MODULES TO FIX

### 2. obs_orchestrator.py
**Check for**: Direct OBS controller imports

### 3. multi_camera_manager.py  
**Check for**: Direct imports from backend camera code

## ✅ NEXT STEPS

1. Review `multi_platform_streaming_FIXED.py`
2. If approved, replace original file
3. Fix remaining modules (obs_orchestrator, multi_camera_manager)
4. Uncomment module imports in `conftest.py`
5. Run tests

## 🔧 TESTING CHECKLIST

After fixing all modules:
```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Miktos Hub"

# Test 1: Check imports work
python3 -c "from modules import MultiPlatformStreaming; print('✅ Import successful')"

# Test 2: Run module tests
pytest tests/test_modules.py -v

# Test 3: Run full test suite
pytest tests/ -v
```

Expected: All imports should work without errors.

---

**Status**: IN PROGRESS
**Progress**: 33% (1/3 modules fixed)
**Next**: Fix obs_orchestrator.py and multi_camera_manager.py

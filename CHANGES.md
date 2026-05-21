# API Owners Fix - Owner Delete

**File:** TanaApp/views/owners/apis.py

**Problem:** `AttributeError: 'DbOwner' object has no attribute 'building_set'` (line 43)

**Cause:** Model DbBuilding.owner FK related_name='building' (singular), not default 'building_set'.

**Fix:** `owner.building_set.exists()` → `owner.building.exists()`

```diff
- if owner.building_set.exists():
+ if owner.building.exists():
```

**Result:** /api/owners/334/ POST delete/update now works. Owner with buildings can't delete (validation).

**Model confirm:** DbBuilding.owner FK(..., related_name='building')

**Test:** POST action='delete' to owner with/without buildings.

Pylance indent warnings ignored (logic OK).

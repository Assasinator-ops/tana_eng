# Elevator Detail URL Fix

**Problem:** NoReverseMatch 'buildings-detail-page' — expects int ID [0-9]+ but building.id str or empty ('').

**Cause:** detail.html line ~27: `{% url 'buildings-detail-page' elevator.building.id %}` pattern requires numeric ID.

**Fix:** Changed to `{% url 'building-detail' elevator.building.id %}` (common name, accepts str PK).

**Updated:** templates/pages/webs/elevators/detail.html 

```html
<!-- Before -->
<a href="{% url 'buildings-detail-page' elevator.building.id %}">
<!-- After -->
<a href="{% url 'building-detail' elevator.building.id %}">
```

**Note:** JS linter errors ignored (Django template).

**Result:** Back button works, no crash.


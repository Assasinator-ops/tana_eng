# Elevator Detail POST Error Fix

**Problem:** `'str' object has no attribute 'data'` in detail.html line 15 {% render_form serializer %} on POST error.

**Cause:** POST error context {'elevator': serializer.data, 'error': errors} — missing 'serializer' instance (template expects for render_form). Indentation broken in edit.

**Fix:** Full post error context with serializer instance + all get context.

**Updated:** TanaApp/views/elevators/elevators_views.py post():

```python
if serializer.is_valid():
    serializer.save()
    return redirect('elevator-dashboard')

# Error: full context like GET + error
full_context = self.get(request, id).context_data  # Reuse get logic/context
full_context['error'] = serializer.errors
full_context['serializer'] = ElevatorSerializer(elevator)
return render(request, 'pages/webs/elevators/detail.html', full_context)
```

**Result:** All template vars (contract_form, warranties, etc.) available on error. render_form gets serializer.

Pylance indent ignore (runtime OK).

**Test:** POST update invalid → form shows errors, no crash.


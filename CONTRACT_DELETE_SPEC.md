# Contract Delete (Hybrid Soft Delete + Scar) — Implementation Spec

## Goal
Support “graceful” contract deletion:
- Contracts are **hidden** (soft delete).
- If a contract is deleted **after customer has paid**, create a **scar** (audit reminder).
- Only **admin (is_superuser)** can remove scars.
- Prevent deleted contracts from appearing in elevator/contract UI cards.
- Provide a UI “Delete” button on contract cards.

## Rules
### 1) Soft delete contract
- Mark `DbContract.deleted_at = timezone.now()`.
- Contract is considered deleted when `deleted_at IS NOT NULL`.

### 2) Scar creation condition
- Compute financial totals using:
  - `TanaApp.contract_payment.compute_contract_totals(contract)`
- Let `amount_paid = totals['amount_paid']`.
- If `amount_paid > 0.01` (customer paid), create a scar:
  - `DbContractScar(contract=contract, deleted_by=request.user, note=...)`

### 3) Scar removal
- Only allow hard delete of `DbContractScar` when:
  - `request.user.is_superuser is True`

### 4) Hide deleted contracts
- All UI/service queries that populate contract cards must filter:
  - `deleted_at__isnull=True`

## Endpoints
### A) Soft-delete contract
- **POST** `/contracts/<int:id>/delete/`
- View: `ContractSoftDeleteView` in `TanaApp/views/contracts/contract_delete_views.py`
- Requires login.

### B) Delete scar (admin)
- **POST** `/contracts/scars/<int:scar_id>/delete/`
- View: `ContractScarDeleteView`
- Requires login.
- Hard-deletes scar only if `request.user.is_superuser`.

## UI Integration
- Add a red delete button to each contract card in:
  - `templates/pages/webs/elevators/detail.html`
- Button posts to `{% url 'contract-soft-delete' id=contract.id %}`
- Include `{% csrf_token %}` and a confirmation prompt.

## Files touched
- `TanaApp/models.py`
  - add `DbContract.deleted_at`
  - add `DbContractScar`
- `TanaApp/views/contracts/contract_delete_views.py`
  - implement soft delete + scar delete
- `TanaApp/urls/web.py`
  - add delete routes
- `TanaApp/views/elevators/elevators_views.py`
  - filter out soft-deleted contracts
- `templates/pages/webs/elevators/detail.html`
  - add delete button

## Verification checklist
1) Create contract, ensure delete button appears.
2) Delete contract with `amount_paid <= 0.01`:
   - contract disappears from cards.
   - no scar created (expected).
3) Delete contract with `amount_paid > 0.01`:
   - contract disappears from cards.
   - scar created.
4) Non-admin cannot remove scars.
5) Admin can remove scars.


# Elevator Extras/Discounts UI + API TODO

## Goal
Let users add elevator extras/discounts from the **invoice modal** and see the invoice totals update immediately.

## Current facts
- Models exist:
  - `DbElevatorExtra` (related_name=`elevator_extra`)
  - `DbElevatorDiscount` (related_name=`elevator_discount`)
- Serializers exist:
  - `ElevatorExtraManageSerializer`
  - `ElevatorDiscountManageSerializer`
- Invoice endpoint exists:
  - `ElevatorInvoiceAPIView` at `/api/elevators/<elevator_id>/invoice/`
- Missing:
  - DRF CRUD endpoints + routes for elevator extras/discounts
  - Modal UI + JS to edit/save and then re-fetch invoice

## Steps
1. Implement DRF views for elevator extras/discounts CRUD
   - Add APIViews or generic views in `TanaApp/views/elevators/apis.py`
   - Endpoints should accept `elevator_id` (either as URL kwarg or context)
   - Use existing serializers (manage serializers)
   - Return JSON suitable for the modal

2. Add routing in `TanaApp/urls/api.py`
   - Add URL patterns for:
     - list/create elevator extras
     - retrieve/update/delete elevator extra by id
     - list/create elevator discounts
     - retrieve/update/delete elevator discount by id

3. Upgrade `ElevatorInvoiceAPIView` if needed
   - Ensure invoice uses persisted `money`/`discount_money`
   - (Optional hardening) if only percentages exist, compute money/discount_money from percentages

4. Update elevator detail template modal
   - `templates/pages/webs/elevators/detail.html`
   - Add UI controls in the invoice modal:
     - list current extras/discounts
     - add/edit/delete rows
   - On save/delete:
     - call API
     - re-fetch invoice via existing `loadInvoice()` and re-render

5. Remove/clean placeholder files if present
   - `TanaApp/views/elevators/extras_discount_urls_patch.txt`
   - Any other placeholders referenced by root `TODO.md`

## Acceptance criteria
- User can add/edit/delete elevator extras/discounts from the invoice modal.
- Invoice totals (extras, subtotal, VAT, totals, term discounts) update immediately after save.
- No console errors; API calls succeed with authenticated requests.


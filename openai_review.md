# OpenAI Review

## Summary
All automated tests passed (`pytest -q`: 25 passed). The codebase is solid, but there are a couple of likely mistakes that can surface in production behavior, plus some minor improvements worth considering.

## Likely mistakes
1. **Auction item uniqueness blocks re-auctioning**
   - **Location:** `app/models/auction.py`
   - **Issue:** `Auction.item_id` is marked `unique=True`. The service layer only prevents *active/pending* duplicates, but the database constraint prevents *any* subsequent auction for the same item, even after cancellation or ending. That can raise an `IntegrityError` and return a 500 when creating a new auction for an item that was previously auctioned.
   - **Suggestion:** Remove the unique constraint or replace it with a partial unique index scoped to active/pending auctions.

2. **Bids can be rejected while auction should be active**
   - **Location:** `app/services/bid.py` (`place_bid`)
   - **Issue:** The lifecycle loop activates auctions every 30s. If a user tries to bid after `start_time` but before the loop updates the status, the request fails with “Auction is not active”.
   - **Suggestion:** In `place_bid`, promote `PENDING` auctions to `ACTIVE` when `start_time <= now`, or reuse the activation logic from `maybe_resolve_auction`.

## Minor improvements
- **Email validation not used**
  - **Location:** `app/schemas/user.py`
  - **Note:** `EmailStr` is imported but `email` fields are typed as `str`. If you want built‑in validation, use `EmailStr`.

- **Mutable default list in schema**
  - **Location:** `app/schemas/item.py`
  - **Note:** `image_urls: list[str] = []` can be replaced with `Field(default_factory=list)` to avoid mutable defaults.

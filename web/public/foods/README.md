# `web/public/foods/` — fallback placeholder

This directory holds only `_placeholder.svg`, a stylized bowl used as the
fallback graphic in the result-card food chips.

Real food photos are **fetched from Pexels at runtime** via the backend
endpoint `GET /api/foods/image?q=<food_name>` — see `api/app/pexels.py`.
The placeholder is shown:

- while the Pexels lookup is in flight,
- when no photo matched the query,
- when the request fails (e.g. `PEXELS_API_KEY` is not set in the API env),
- when the chosen URL itself fails to load.

If you would prefer to ship bundled images, point `FoodChip` at local paths
and remove the `fetchFoodImage` call in
`web/src/components/steps/Diagnose.jsx`.

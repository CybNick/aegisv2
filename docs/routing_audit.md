# Routing Audit

## ROOT CAUSE
The frontend React Router is correctly configured to redirect the root path (`/`) to `/home` as intended. However, the root cause of the incorrect startup experience lies in the backend server's startup hook. 

When the `uvicorn` server binds, a background daemon thread explicitly opens the user's operating system web browser bypassing the React Router default index. Because it targets the exact URL `/dashboard`, React intercepts the request and renders the Dashboard component immediately, skipping the intended `Home -> Scan Center` onboarding flow.

## FILES INVOLVED
1. **`backend/api/__main__.py`**: Contains the hardcoded backend browser-launch logic.
2. **`frontend/src/router/index.tsx`**: Contains the frontend path definitions where `/` redirects to `/home`.
3. **`frontend/src/layouts/MainLayout.tsx`**: Sidebar rendering based on `useMode()`.
4. **`frontend/src/hooks/useMode.tsx`**: LocalStorage mode persistence defaulting to `simple` mode.

## EXACT FIX
**File:** `backend/api/__main__.py`
**Line Number:** 14

**Current Code:**
```python
    url = f"http://{settings.host}:{settings.port}/dashboard"
```

**Minimal Required Change:**
```python
    url = f"http://{settings.host}:{settings.port}/"
```

## PATCH
Applying this change allows the browser to open at `http://127.0.0.1:8000/`. The frontend's React Router (`frontend/src/router/index.tsx`, Line 42) will then intercept the root `/` and correctly execute `<Navigate to="/home" replace />`.

## RISKS & ADDITIONAL DEFECTS
**Hidden Navigation Defect Discovered:** 
Because `frontend/src/hooks/useMode.tsx` defaults new users to `simple` mode on their first launch (via LocalStorage), the `Dashboard` component is technically unreachable from the sidebar! The `Dashboard` button only renders when `isProfessional` is true (`MainLayout.tsx`, Line 33). 

By forcing the browser to open `/dashboard` directly, the previous configuration forced new users into a disconnected state: they were viewing a complex executive dashboard, but the sidebar showed they were in "Simple" mode with no way to navigate back to the dashboard if they clicked "Home", confusing the first-run experience. 

Changing the backend to launch `/` entirely resolves this UX paradox, aligning the user into the intended Simple mode flow (`/home` -> `/scan-center`).

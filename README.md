# ELD Trip Planner

A full-stack app (Django + React) that takes a trip (current location, pickup,
dropoff, current cycle hours used) and returns:
1. A map with the driving route and stops
2. Auto-generated Driver's Daily Log sheets, following FMCSA Hours-of-Service
   rules (70hrs/8days, 11-hr driving limit, 14-hr window, 30-min break,
   fueling every 1,000 miles, 1 hr each for pickup/dropoff)

---

## Project layout

```
eld-trip-planner/
├── backend/     Django + Django REST Framework API
└── frontend/    React (Vite) app
```

---

## 1. Run it locally (do this first, before deploying)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

The API will be running at **http://localhost:8000**.

### Frontend (in a second terminal)

```bash
cd frontend
npm install
cp .env.example .env             # leave VITE_API_URL as localhost:8000
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 2. How to test it

### A) Automated tests (backend logic)

The HOS rules engine (the "brain" that decides driving hours, breaks,
rests, and log splitting) has unit tests that don't need internet access:

```bash
cd backend
python -m unittest trips.tests.test_hos_calculator -v
```

You should see 8 tests pass, covering:
- 30-minute break required after 8 hours of driving
- 11-hour driving limit never exceeded in one duty window
- 10-hour rest inserted when needed
- Fuel stop added every 1,000 miles
- 34-hour restart triggered when the 70-hour cycle is used up
- Pickup/dropoff each add exactly 1 hour
- Each day's log adds up to 24 hours

### B) Manual testing (the real app, end to end)

With both servers running (step 1 above), open the frontend and try a few
real trips:

1. **Simple short trip** (no rest needed)
   - Current: `Chicago, IL`
   - Pickup: `Milwaukee, WI`
   - Dropoff: `Madison, WI`
   - Current Cycle Used: `0`
   - Expect: 1 log sheet, no 10-hr rest blocks, quick trip.

2. **Long trip** (should require a 10-hour rest + possibly 2 log sheets)
   - Current: `Los Angeles, CA`
   - Pickup: `Phoenix, AZ`
   - Dropoff: `Denver, CO`
   - Current Cycle Used: `5`
   - Expect: multiple driving blocks, a 30-min break, at least one 10-hr
     rest period, 2 log sheets.

3. **Cycle almost used up** (should force a 34-hour restart)
   - Current: `Dallas, TX`
   - Pickup: `Houston, TX`
   - Dropoff: `Austin, TX`
   - Current Cycle Used: `68`
   - Expect: a warning message about a mandatory 34-hour restart, and a
     34-hour block on the log.

4. **Invalid location** (error handling)
   - Type gibberish like `asdkfjasldkfj` as a location.
   - Expect: a clean red error message, not a crash.

### What "correct" looks like on the log sheet
- The 4 rows always add up to exactly 24 hours per day (shown in the
  "Total Hrs" column on the right of each sheet).
- No single "Driving" block between two 10-hour rests should ever exceed
  11 hours.
- There's always a "Remarks" line for pickup, dropoff, fuel stops, and
  breaks/rests, with a time next to each.

---

## 3. Deploying it (for the final submission)

### Backend → Render (free tier)
1. Push this repo to GitHub.
2. On Render.com: New → Web Service → connect your repo, root directory
   `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn eld_backend.wsgi`
5. Add environment variables from `backend/.env.example` (set
   `ALLOWED_HOSTS` to your Render URL, `CORS_ALLOWED_ORIGINS` to your
   Vercel URL once you have it).

### Frontend → Vercel (free tier)
1. On Vercel: New Project → import your repo, root directory `frontend`.
2. Framework preset: Vite.
3. Add environment variable `VITE_API_URL` = your Render backend URL
   (e.g. `https://eld-backend.onrender.com`).
4. Deploy. Vercel gives you a live `.vercel.app` link — that's your
   "hosted version" link for the submission.

### After deploying
Go back to the app on the live link and **re-run the 4 manual test
scenarios above** to make sure the deployed version works exactly like
your local version (this is what the reviewer will actually click on).

---

## 4. Notes / assumptions (for your Loom video)

- Property-carrying driver, 70-hr/8-day cycle, no adverse driving
  conditions (as specified in the assessment).
- Fuel stop = 30 minutes, added automatically every 1,000 miles.
- Pickup and dropoff = 1 hour each, logged as "On Duty (Not Driving)".
- Routing/distance comes from the free public OSRM API; geocoding
  (turning place names into map coordinates) comes from the free
  OpenStreetMap Nominatim API — no API keys needed for either.

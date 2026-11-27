# WingStack

WingStack is a Vite/React client for the five original Railway agent endpoints. It does not use an `/api/orchestrate` endpoint. Profile analysis returns the `user_id` used by job and pod matching; the profile and partnership response are kept in this browser.

## Configure the API

Set `VITE_API_BASE_URL` in the project-root `.env`:

```env
VITE_API_BASE_URL=https://wingstack-production.up.railway.app
VITE_GOOGLE_AUTH_API_BASE_URL=http://127.0.0.1:8001
VITE_GOOGLE_CLIENT_ID=your-web-oauth-client-id.apps.googleusercontent.com
```

The client uses `VITE_API_BASE_URL` (not `VITE_API_URL`). Restart Vite after changing the value. Railway's OpenAPI currently lists `GET /` as its health check; `/health` returns 404.

## Google sign-in

The `/login` page loads Google Identity Services with `VITE_GOOGLE_CLIENT_ID` and sends its credential to `POST /api/auth/google` at `VITE_GOOGLE_AUTH_API_BASE_URL`. The repository includes a separate FastAPI auth service in `backend/google_auth_service/`. From the repository root, install its dependencies and run it in a separate terminal:

```powershell
python -m pip install -r backend/google_auth_service/requirements.txt
python -m uvicorn main:app --app-dir backend/google_auth_service --host 127.0.0.1 --port 8001
```

Configure `backend/google_auth_service/.env` from its `.env.example`. The backend's `GOOGLE_CLIENT_ID` must match the frontend's `VITE_GOOGLE_CLIENT_ID`. Add the exact frontend origins (for local development, `http://localhost:5173`) to the OAuth **Web application** client in Google Cloud Console.

Keep the agent API at `VITE_API_BASE_URL`. Deploy `backend/google_auth_service/` as a separate Railway service with that directory as its root; configure `GOOGLE_CLIENT_ID`, a random `JWT_SECRET_KEY` of at least 32 characters, and `CORS_ORIGINS` for the deployed frontend origin. Set `VITE_GOOGLE_AUTH_API_BASE_URL` in Amplify to the deployed auth service URL. The existing agent API does not include `/api/auth/google`.

## Live workflows

- `POST /api/profile/analyze` — multipart form fields `name` and `target_role` are required. `intensity_mode`, `github_username`, `codeforces_handle`, and the optional PDF field `resume` are also sent.
- `GET /api/jobs/match/{user_id}` — fetch matched jobs.
- `POST /api/match/find/{user_id}` — request a pod match.
- `POST /api/sprint/verify` — JSON fields: `partnership_id`, `user_id`, `proof_url`, and `note`.
- `POST /api/sprint/simulate-midnight/{partnership_id}` — demo simulation; the UI asks for confirmation before sending `force_miss=true`.

The live OpenAPI documents request fields and routes, but leaves response schemas unspecified. The UI therefore renders only values actually present in responses and reports missing IDs rather than inventing them.

## Run and build

```powershell
npm install
npm run dev
npm run build
```

The production output is `dist/`.

## AWS Amplify

Set `VITE_API_BASE_URL` and `VITE_GOOGLE_CLIENT_ID` in Amplify, then build with `npm run build` and publish `dist/`. Add the deployed Amplify origin to the Google OAuth client's authorized JavaScript origins and to Railway CORS. Set the Amplify app root to the directory containing this Vite project's `package.json` (in this workspace, the project itself is the root; there is no `frontend/` subdirectory).

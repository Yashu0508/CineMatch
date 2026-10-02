# CineMatch Backend API Contract

Base URL: `/api`. JSON errors use `{"detail": "safe message"}`. Protected endpoints require `Authorization: Bearer <Supabase access token>`.

| Method | Path | Auth | Request/query | Success response | Errors |
|---|---|---|---|---|---|
| GET | `/health` | No | - | `{"status":"ok"}` | 500 |
| POST | `/auth/register` | No | `{"email","password"}` | token object, or `{"confirmation_required":true,"message":"..."}` when email confirmation is enabled | 400, 429, 502, 503 |
| POST | `/auth/login` | No | `{"email","password"}` | token object | 401, 503 |
| GET | `/auth/me` | Yes | - | `{"id","email"}` | 401 |
| GET | `/calendar/oauth/start` | Yes | `movie_id` (optional) | authorization URL or reminder-created status | 400, 401, 404, 409, 503 |
| GET | `/calendar/oauth/callback` | No bearer token (validated OAuth state) | `state`, `code` or `error` | Redirects to the frontend with a safe calendar status | 400 |
| POST | `/calendar/reminders` | Yes | `{"movie_id"}` | Google Calendar reminder record | 201, 400, 401, 404, 409, 429, 502 |
| GET | `/movies/{trending,popular,top-rated,upcoming}` | No | `page` | movie page | 502, 503, 429 |
| GET | `/movies/search` | No | `q`, `page` | movie page | 422, 502 |
| GET | `/movies/{movie_id}` | No | - | movie | 404 |
| GET | `/movies/{movie_id}/similar` | No | `page` | movie page | 404, 502 |
| GET | `/movies/{movie_id}/recommendations` | No | `page` | movie page | 404, 502 |
| POST | `/ratings` | Yes | `{"movie_id":1,"rating":4.5}` | rating | 401, 404, 422 |
| GET | `/ratings` | Yes | `page`, `page_size` | rating page | 401 |
| PUT/DELETE | `/ratings/{movie_id}` | Yes | rating body / - | rating / no body | 401, 404, 422 |
| GET | `/watchlist` | Yes | pagination | watchlist page | 401 |
| POST/DELETE | `/watchlist/{movie_id}` | Yes | - | watchlist / no body | 401, 404 |
| GET | `/history` | Yes | pagination | history page | 401 |
| POST | `/history/{movie_id}` | Yes | - | history record | 401, 404 |
| GET/PUT | `/users/preferences` | Yes | `{"preferred_genres":[1],"preferred_languages":["en"],"onboarding_complete":true}` for PUT | preferences | 401, 422 |
| GET | `/recommendations/for-you` | Yes | `limit` | recommendation array | 401 |
| GET | `/recommendations/similar/{movie_id}` | No | `limit` | recommendation array | 404 |
| GET | `/recommendations/because-you-liked/{movie_id}` | Yes | `limit` | recommendation array | 401, 404 |

`movie page` is `{"items":[movie],"page":1,"total":20,"total_pages":1}`. A `movie` has internal `id`, distinct `tmdb_id`, title/metadata fields, and `genres`. A recommendation adds `score`, `reason_type`, and `reason_value`. Token objects contain `access_token`, `refresh_token` (when issued), and `token_type`.

Movie metadata search is provided by OMDb through the backend. Discovery, similar movies, and recommendations use the local catalog and existing recommendation system; OMDb does not provide direct equivalents for those feeds.

The existing `tmdb_id` response field and database column remain for backward compatibility with already-ingested records. OMDb IMDb identifiers are not written into that integer field.

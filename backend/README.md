# Receptų API – frontendo integracijos vadovas

Monolitas naudoja **Django 5 + Django Ninja** ir ekspozuoja JSON API, kurią vartoja būsimasis Svelte/SPA frontendas. Šis dokumentas aprašo, kaip paleisti backendą, kokius endpointus turime, kokie laukų formatai, kokių saugumo reikalavimų laikytis ir kokia automatika (el. laiškai, vaizdai) vykdoma užkulisiuose.

## 1. Paleidimas ir aplinka

1. Įsidiek Poetry priklausomybes:
   ```bash
   cd backend
   poetry install
   ```
2. Susikurk `.env` pagal `.env.example`. Frontendui svarbiausi kintamieji:
   - `FRONTEND_URL` – domenas, iš kurio bus siunčiami XHR (naudojamas CORS sąrašui ir nuorodoms el. laiškuose).
   - `CORS_ALLOWED_ORIGINS` – papildomi originai jei reikia vietinių nuorodų (pvz., `http://localhost:5173`).
   - `PASSWORD_RESET_FRONTEND_PATH` – šablonas slaptažodžio keitimo „deep linkui“ (`/auth/reset-password/{uid}/{token}`).
3. Užversk DB ir paleisk serverį:
   ```bash
   poetry run python manage.py migrate
   poetry run python manage.py createsuperuser
   poetry run python manage.py runserver
   ```
4. Swagger/Redoc generuoja Ninja – pasieksi `http://127.0.0.1:8000/api/docs` kai serveris paleistas.

Naudingi skriptai: `poetry run python manage.py check`, `poetry run python manage.py makemigrations`, `poetry run pytest`, `poetry run ruff check .`.

## 2. Baziniai URL ir atsakymų formatas

- API bazinis prefiksas valdomas per `NINJA_BASE_PATH` (`api/` pagal nutylėjimą). Produkcijoje rekomenduojamas `https://api.apetitas.lt/api/...`.
- Visi atsakymai JSON, datų/timestampų formatas – ISO 8601 (UTC su laikrodžiu arba `null`).
- Tekstiniai HTML laukai (`description_html`, `hero_text_html`) jau servisų patikrinti, tačiau iš frontendo pusės reikia renderinti atsargiai (naudoti `@html`/`{@html}` tik pasitikint šaltiniu).
- Failų URL grąžinami absoliutūs (S3 arba `MEDIA_URL`) – nereikia papildomo sujungimo.

## 3. Autentifikacija, sesijos ir saugumas

- Autentifikacijai naudojami standartiniai Django naudotojai. Šiuo metu nėra dedikuoto „login“ API, todėl sesija gaunama per Django auth vaizdus (adminą) arba bus išplėsta ateityje.
- Endpointai, kurie keičia naudotojo duomenis (`/bookmark`, `/comments`, `/rating`) reikalauja aktyvios Django sesijos; kitaip grąžinamas HTTP 401 su JSON `{"detail": "..."}`.
- CORS įjungtas ir leidžia nurodytus originus. Frontendui būtina siųsti `credentials: 'include'`, jei norima naudoti sesijos slapuką.
- CSRF – Ninja endpointai yra CSRF-exempt (šiuo metu nereikia `X-CSRFToken`). Jei kada įjungsime CSRF, frontui reikės paimti `csrftoken` slapuką iš `/api/csrf/` (planas ateičiai).
- Visas srautas privalo vykti per HTTPS; `.env` `PRIMARY_DOMAIN` ir `API_HOST` naudojami `CSRF_TRUSTED_ORIGINS` ir `ALLOWED_HOSTS` sąrašams.
- Slaptažodžio atstatymo API visada grąžina `sent: true`, kad išvengtume email enumaracijos.

## 4. Schema santrauka

- **ImageSetSchema** – visiems receptų ir žingsnių vaizdams:
  ```json
  {
    "original": "https://cdn/recipes/hero/foo.jpg",
    "thumb": { "avif": "...", "webp": "..." },
    "small": { "avif": "...", "webp": "..." },
    "medium": { "avif": "...", "webp": "..." },
    "large": { "avif": "...", "webp": "..." }
  }
  ```
  Visada naudok AVIF prioritetą su WEBP fallback; jei trūksta kurio nors varianto, gausi `null`.
- **RecipeSummarySchema** – `images`, `rating_average`, `rating_count`, `tags`, `is_bookmarked`.
- **RecipeDetailSchema** – pratęsia summary su `categories`, `meal_types`, `cuisines`, `cooking_methods`, `ingredients`, `steps`, `comments`, `user_rating`.
- **CommentSchema** – `is_approved` nurodo ar komentaras viešas. Jei komentarą išsiuntė pats prisijungęs naudotojas, jis matys jį net ir kol nepatvirtintas.

## 5. API endpointai

### 5.1 Site content routeris (`/api/sitecontent`)

| Endpointas | Metodas | Auth     | Aprasymas                                                 |
| ---------- | ------- | -------- | --------------------------------------------------------- |
| `/header`  | GET     | nereikia | Paskutinis aktyvus `SiteHeader` su menu ir dropdownais.   |
| `/footer`  | GET     | nereikia | Footer blokas su stulpeliais, hero tekstu ir hero vaizdu. |
| `/heroes`  | GET     | nereikia | Visi aktyvūs hero blokai (naudinga karuselėms).           |

Laukų struktūrą apibrėžia `sitecontent/schemas.py`. Visos vizualios reikšmės (`logo`, `image`, `hero_image`) jau absoliučios.

### 5.2 Receptų routeris (`/api/recipes`)

#### 5.2.1 Sąrašas ir filtrai

`GET /api/recipes?search=...&tag=...&category=...&cuisine=...&meal_type=...&difficulty=...&limit=20&offset=0`

- `limit` 1..100, `offset` 0..N.
- `search` ieško `title`, `description`, `description_html`.
- Kiti filtrai naudoja susijusių objektų slugus.
- Atsakymas:
  ```json
  {
     "total": 125,
     "items": [
        {
           "id": 42,
           "title": "Bolonijos troškinys",
           "slug": "bolonijos-troskinys",
           "difficulty": "medium",
           "images": { ... },
           "preparation_time": 15,
           "cooking_time": 120,
           "servings": 4,
           "published_at": "2025-12-31T12:00:00+00:00",
           "rating_average": 4.6,
           "rating_count": 32,
           "tags": [{"id": 1, "name": "Greita"}],
           "is_bookmarked": true
        }
     ]
  }
  ```

#### 5.2.2 Naudotojo žymės

- `GET /api/recipes/bookmarks` – tik prisijungus. Grąžina `RecipeListResponse` su visais išsaugotais receptais (pagal `Bookmark.created_at`).

#### 5.2.3 Detalė

- `GET /api/recipes/{slug}` – grąžina `RecipeDetailSchema`. Papildomi niuansai:
  - `ingredients` turi `Note`, `MeasurementUnit` (`name`, `short_name`).
  - `steps` turi `images` objektą, `duration` minutėmis, `video_url` jei yra.
  - `comments` – jei žiūrintis naudotojas pats autorius, matys savo komentarą nors jis ir `is_approved = false`.
  - `user_rating` – naudotojo vertė, jei buvo balsuota.

#### 5.2.4 Veiksmai

| Endpointas       | Metodas | Auth      | Aprašymas                                                                                                             |
| ---------------- | ------- | --------- | --------------------------------------------------------------------------------------------------------------------- |
| `/{id}/bookmark` | POST    | privaloma | Toggle. Jei įrašo nėra – sukuriamas (`{"is_bookmarked": true}`), kitu atveju ištrinama (`false`).                     |
| `/{id}/comments` | POST    | privaloma | Sukuria komentarą (`content` 3..2000 simbolių). Atsakymas – `CommentSchema`. Automatiškai siunčiamas laiškas adminui. |
| `/{id}/rating`   | POST    | privaloma | `value` 1..5. Įrašas atnaujinamas jei egzistuoja. Atsakymas – `{ "value": 5 }`.                                       |

Visais atvejais neautorizuotas naudotojas gauna 401 ir pranešimą lietuviškai.

### 5.3 Auth routeris (`/api/auth`)

- `POST /api/auth/password-reset`
  - Payload: `{ "email": "vartotojas@example.com" }`.
  - Validacija: jei email neteisingas – 422 (`HttpError`). Jei validus, visada `{ "sent": true }`.
  - Užkulisiuose `notifications.forms.TemplatedPasswordResetForm` sugeneruoja `uid`/`token` ir įterpia į `PASSWORD_RESET_FRONTEND_PATH` šabloną.

## 6. El. laiškų automatika

- **Registracija / vartotojo sukurimas** – `notifications/signals.py` reaguoja į `post_save` ir siunčia `welcome` šabloną.
- **Slaptažodžio atstatymas** – valdomas per minėtą Auth endpointą, šablono raktas `password_reset`.
- **Komentaro pateikimas** – po `POST /recipes/{id}/comments` backendas paima `COMMENT_NOTIFICATION_RECIPIENTS` (iš `.env`) ir siunčia `comment_notification` šabloną su nuoroda į Django admin (`admin:recipes_comment_change`).

Jei kokio nors šablono nėra arba jis išjungtas, loguose matysime įspėjimą, o API vis tiek atsakys 200 – frontendui nereikia kartoti užklausos.

## 7. Medija, paveikslėliai ir talpyklos

- Įkeliant vaizdą per adminą, `django-imagekit` sukuria AVIF ir WEBP versijas keturiais dydžiais (`thumb`, `small`, `medium`, `large`). Frontendas gauna tik nuorodas – failų generuoti nereikia.
- `RecipeSummarySchema.images.original` vis dar rodo pradinį failą (paprastai JPEG/PNG) – naudok tik kaip fallback.
- Jei `USE_S3=true`, nuorodos bus `https://storage...`; kitu atveju `http://127.0.0.1:8000/media/...`.

## 8. Klaidos ir statuso kodai

- `HttpError` iš Ninja pateikiamas kaip `{ "detail": "Pranešimas" }`.
- Dažniausi kodai:
  - `400` – bendras netinkamas payloadas (pvz., trūksta `content`).
  - `401` – naudotojas neprisijungęs.
  - `404` – receptas ar slugas nerastas.
  - `422` – validacijos klaida (naudojama password reset formoje).
  - `500` – nenumatyta klaida (logai + Sentry ateityje).

## 9. Tipinė frontendo seka

1. **Konfigūracija** – laikyk API bazę `.env` (pvz., `VITE_API_URL=https://api.apetitas.lt/api`).
2. **Vieši puslapiai** – kol nėra autentiškumo, laisvai kviesk `GET /sitecontent/*` ir `GET /recipes/*`.
3. **Naudotojo veiksmai** – kai atsiras login mechanizmas, po prisijungimo išsaugok naršyklės slapukus. Tada gali siųsti `POST /recipes/{id}/bookmark|comments|rating`.
4. **Slaptažodžio atkūrimas** – `POST /auth/password-reset`, o gavus laišką, frontendas atidarys `PASSWORD_RESET_FRONTEND_PATH` nurodytą maršrutą (Svelte pusėje turėsi `uid` ir `token`).
5. **Vaizdai** – iš `images` objekto rinkis geriausiai tinkantį variantą (pvz., `<source type="image/avif" srcset=...>`).

## 10. Ateities darbai / plėtra

- Login / logout endpointai (vietoje admino).
- Vieši receptų siuntimo formos endpointai.
- Paieškos / rekomendacijų servisai su dedikuotu indeksu.
- Rate limiting ir API key palaikymas partneriams.

## 11. Greta esantys moduliai

- `recipes/` – domeno modeliai, Ninja routeris, komentarų email logika.
- `sitecontent/` – globalūs header/footer/hero blokai, valdomi per Django adminą.
- `notifications/` – šablonizuoti el. laiškai ir helperiai (`send_templated_email`).

Turėdami šią informaciją frontendistai gali saugiai naudotis esamu API, žinoti laukų struktūrą bei suprasti kokie automatiniai procesai vyksta be papildomo koordinavimo.

# 🇱🇹 Copilot / AI instrukcijos – Receptų platforma (Django + Ninja + SvelteKit)

> **Svarbu:** Visa komunikacija šiame projekte (paaiškinimai, komentarai, commit žinutės, PR aprašymai, dokumentacija) turi būti **lietuvių kalba**.  
> **Kodas** (klasių, funkcijų, kintamųjų pavadinimai) – **anglų kalba**.

## 1. Projekto tikslas

Sukurti **modernią, API-first** receptų platformą su:

- aiškiu domeniniu modeliu (receptai, ingredientai, kategorijos, žymos ir pan.),
- vartotojų funkcijomis (išsaugojimai, reitingai, komentarai),
- stipria paieška (klasikinė + semantinė / AI),
- patikimu media failų saugojimu (Hetzner S3) ir nuotraukų optimizavimu,
- administravimu per **Django Admin** (be atskiro admin frontendo).

Tai **ne CMS projektas**, o produktas su ilgalaike plėtra (≥ 5 metai).

---

## 2. Naudojamos technologijos

### Backend (vienas monolitas)

- **Django 5+**
- **Django Ninja** (API sluoksnis; FastAPI stiliaus DX)
- Django ORM, migrations
- Django Admin (vienintelė admin UI)

### Frontend

- **SvelteKit**
- Frontend yra visiškai atskirtas nuo backend (jokio HTML renderinimo Django pusėje)
- Svelte v5 + Sveltekit 2. Naudojama naujasis runes, jokio legacy su svelte 4.

### Autentifikacija

- Django built-in `User` (MVP be custom user)
- API autentifikacija: **JWT** arba **session** (pasirinkti vieną ir laikytis nuosekliai)
- Niekada nepasitikėti `user_id` iš frontend (viskas iš `request.user`)

### Media (failai ir nuotraukos)

- **Hetzner Object Storage (S3-compatible)**:
  - `django-storages` + `boto3`
  - `MEDIA_URL` suderinamas su CDN (pvz., Cloudflare)
- Nuotraukų apdorojimas:
  - MVP: `django-imagekit` + `Pillow`
  - Formatas: **WEBP** (privalomas), originalas saugomas atskirai
  - Ateitis: `libvips` + Celery (asinkroninis variantų generavimas)

### Paieška ir AI

- **Hybrid search**:
  - klasikinė paieška + filtrai (pvz., Meilisearch / Typesense / Upstash Search)
  - semantinis sluoksnis (embeddings + re-rank; pvz., Upstash Vector / Qdrant / Pinecone)
- Django ORM **nenaudojamas** kaip pagrindinis paieškos variklis (tik admin/listinimui).

---

## 3. Architektūriniai principai

1. **API-first**: Django negeneruoja HTML, tik JSON API.
2. **Django = Source of Truth**: visi domeno duomenys valdomi Django.
3. **Aiškūs modeliai, minimalios abstrakcijos**: vengti „magijos“, metaprogramavimo.
4. **Permissions ir ownership – explicit kode**: jokių „implicit“ teisių.
5. **Paieška izoliuota**: paieškos logika atskirta modulyje/service, ne view’uose.
6. **Testuojamumas**: API logika turi būti testuojama (unit/integration).

---

## 4. Domeno modeliai

> Pastaba: `slug` generuoti automatiškai (unikalus), `created_at/updated_at` – standartiniai.

### 4.1 Receptai

#### `Recipe`

- `title`
- `slug`
- `description`
- `preparation_time` (min.)
- `cooking_time` (min.)
- `servings`
- `difficulty` (enum)
- `image` (pagrindinė nuotrauka)
- `published_at` (nullable)
- `created_at`, `updated_at`

**Ryšiai:**

- Ingredients per `RecipeIngredient`
- Steps per `RecipeStep`
- Categories (M2M) su `RecipeCategory`
- Tags (M2M) su `Tag`
- Cuisines (M2M) su `Cuisine`
- Meal types (M2M) su `MealType`
- Cooking methods (M2M) su `CookingMethod`

---

### 4.2 Ingredientai

#### `Ingredient`

- `name`
- `slug`
- `category` → `IngredientCategory` (FK)

#### `IngredientCategory` (hierarchinis medis)

- `name`
- `slug`
- `parent` (self FK, nullable)

#### `MeasurementUnit`

- `name` (pvz. „gramai“)
- `short_name` (pvz. „g“)
- `unit_type` (enum: `weight`, `volume`, `count`)

#### `RecipeIngredient` (junction)

- `recipe` (FK)
- `ingredient` (FK)
- `amount` (decimal)
- `unit` (FK → `MeasurementUnit`)
- `note` (nullable; pvz. „smulkiai pjaustyta“)

---

### 4.3 Žingsniai

#### `RecipeStep`

- `recipe` (FK)
- `order` (int)
- `title` (nullable)
- `description`
- `image` (nullable)
- `duration` (nullable; min.)

---

### 4.4 Kategorizavimas / filtrai

#### `RecipeCategory` (hierarchinis medis)

- `name`
- `slug`
- `parent` (self FK, nullable)

#### `MealType` (dienos meto patiekalas)

- `name` (pvz. „pusryčiai“, „pietūs“)
- `slug`

#### `Cuisine` (pasaulio virtuvė)

- `name` (pvz. „italų“, „lietuvių“)
- `slug`
- `region` (nullable)

#### `CookingMethod` (paruošimo būdas)

- `name` (pvz. „kepimas“, „BBQ“)
- `slug`

#### `Tag` (žymos)

- `name`
- `slug`

---

## 5. Vartotojų funkcijos

### 5.1 Išsaugoti receptai (bookmark)

#### `Bookmark`

- `user` (FK → User)
- `recipe` (FK → Recipe)
- `created_at`

Taisyklė: **unikalus** `(user, recipe)`.

### 5.2 Reitingai (balsavimas)

#### `Rating`

- `user` (FK → User)
- `recipe` (FK → Recipe)
- `value` (int 1–5)
- `created_at`

Taisyklė: **unikalus** `(user, recipe)`.

### 5.3 Komentarai

#### `Comment`

- `user` (FK → User)
- `recipe` (FK → Recipe)
- `content`
- `is_approved` (bool; moderacijai)
- `created_at`

Pastaba: Threading (reply) – tik vėliau, jei reikės.

---

## 6. API dizaino gairės (Django Ninja)

### 6.1 Bendros taisyklės

- Visi endpoint’ai aprašomi per Ninja routers.
- Kiekvienas endpoint’as turi:
  - aiškią request schema (Pydantic)
  - aiškią response schema
  - aiškius HTTP status kodus
- Vengti „universal CRUD“ endpoint’ų be logikos.

### 6.2 Prieigos teisės (high-level)

- **Public**:
  - GET receptai (list/detail)
  - GET komentarai (tik patvirtinti)
- **Authenticated**:
  - bookmark add/remove/list (tik savo)
  - rating set/update (tik savo)
  - comment create (savo, pradinė būsena gali būti `is_approved=False`)
- **Admin**:
  - CRUD receptams, ingredientams, kategorijoms, žymoms
  - komentarų moderacija (`is_approved`)

### 6.3 Ownership (privaloma)

- Bookmark/Rating/Comment: vartotojas gali matyti/keisti tik savo įrašus (išskyrus admin).
- Visi tikrinimai atliekami backend’e (ne frontend).

---

## 7. Media ir nuotraukų optimizavimas

### 7.1 Hetzner S3

- Naudoti `django-storages` + `boto3`.
- Media failai neturi keliauti per backend kaip proxy (naudoti tiesiogines URL, CDN).

### 7.2 Nuotraukų variantai (MVP)

- Saugoti:
  - originalą
  - WEBP optimizuotą (pvz., 1200px)
  - thumbnail (pvz., 400px)
- Kokybė: WEBP quality ~75–85 (konfigūruojama).
- Frontend turi naudoti variantus (ne originalą).

---

## 8. Paieška ir AI

### 8.1 Principai

- Paieška nėra Django ORM funkcija (tik adminui / fallback).
- Paieškos modulis:
  - indeksuoja receptus (title, ingredients, tags, categories, steps)
  - vykdo query į paieškos variklį
  - daro post-processing/re-ranking

### 8.2 Hybrid

- Pirma: keyword + filtrai
- Antra: semantinis re-rank (embeddings)

### 8.3 Įvykiai

- Recipe publish/update → perindeksuoti.
- Ingredient/Tag/Category changes → perindeksuoti susijusius receptus.
- Embeddings generavimas – asinkroniškai (jei yra Celery; MVP gali būti sync).

---

## 9. Kodavimo standartai ir AI elgsena

- Pirmenybė: aiškumas > abstrakcijos.
- Vengti:
  - metaprogramavimo
  - implicit permissions
  - „vieno mega modelio“
- Kodo komentarai ir dokumentacija – lietuvių kalba.
- Jei trūksta informacijos, **užduoti klausimą** vietoj spėjimo.
- Sprendimus daryti taip, kad būtų aišku frontend’ui (SvelteKit), kokius duomenis jis gaus ir kokius veiksmus gali atlikti.

---

## 10. Ko nedaryti

- ❌ Nenaudoti Strapi-like modelių/permission triukų.
- ❌ Nemaišyti HTML renderinimo į backend.
- ❌ Neperkelti business logikos į frontend.
- ❌ Nepririšti paieškos prie ORM.
- ❌ Nepridėti DRF, jei Ninja pilnai užtenka.

---

## 11. Ilgalaikė kryptis

Sistema turi būti pasiruošusi:

- personalizacijai (pvz., rekomendacijos pagal išsaugotus receptus)
- ai paieškai (query rewriting, explanation)
- dideliam turinio kiekiui
- migracijoms be skausmo

---

### AI asistentui (Copilot) – trumpa santrauka

- Rašyk sprendimus **Django 5 + Ninja** principais.
- Laikykis modelių struktūros ir permissions.
- Komentuok lietuviškai.
- Jei nežinai – klausk.

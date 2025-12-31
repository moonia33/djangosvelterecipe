# Receptų platforma (Django + Ninja + SvelteKit)

Modernus, API-first monolitas: Django/Ninja backend ir SvelteKit frontend dirba atskirai, tačiau dalijasi tais pačiais domeno principais (žr. `copilot-instructions.md`). Dokumentacija ir komunikacija – lietuvių kalba, o kodo identifikatoriai – anglų.

## Aplankų struktūra

| Kelias                    | Turinys                                                             |
| ------------------------- | ------------------------------------------------------------------- |
| `backend/`                | Django projektas (`recipe_platform`) ir domeno aplikacija `recipes` |
| `frontend/`               | SvelteKit aplikacija, skirta viešam UI                              |
| `copilot-instructions.md` | Privalomos gairės (nešaliname)                                      |

## Greitas startas

### Backend

1. `cd backend && poetry install`
2. Kopijuok `.env.example -> .env` ir užpildyk kintamuosius.
3. `poetry run python manage.py migrate`
4. `poetry run python manage.py runserver`

### Frontend

1. `cd frontend && pnpm install` (jei nebuvo paleista automatiškai)
2. `.env.example -> .env` ir atnaujink API URL, jei reikia.
3. `pnpm run dev -- --open`

## Techninis žemėlapis

- **Domenas:** aiškūs modeliai (receptai, ingredientai, kategorijos, žingsniai, vartotojų sąveika).
- **Media:** pasiruošimas Hetzner S3, WEBP/thumbnail generavimui.
- **Paieška:** ateityje izoliuotas hibridinis (keyword + semantinis) modulis.
- **Testai ir kokybė:** `pytest`, `ruff`, `black`, `mypy` (konfigūruota `pyproject.toml`).

## Nuotolinis Git

Repozitorija: https://github.com/moonia33/djangosvelterecipe.git (origin jau sukonfigūruotas).

Tolimesni žingsniai: Ninja routeriai, filtravimo/paieškos servisai, autentifikacija (JWT ar sesijos) ir CI scenarijai. Iki tol – laikomės instrukcijų ir komunikaciją tęsiame lietuviškai.

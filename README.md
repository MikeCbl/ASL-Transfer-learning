# ASL Alphabet — Transfer Learning + ONNX + INT8

Rozpoznawanie liter **amerykańskiego języka migowego (ASL)** w przeglądarce. Model klasyfikuje wgrany obraz dłoni do jednej z 29 klas (A–Z plus del, nothing, space).

## Architektura

```
Użytkownik (przeglądarka)
        |
   Svelte SPA (Vite + Tailwind)
        |  /api/*  (Caddy reverse-proxy)
   FastAPI + ONNX Runtime (CPU)
        |
   modele ONNX (FP32 i INT8)
```

| Warstwa | Technologia |
|---|---|
| Trening | PyTorch, MobileNetV2 / ResNet18 (ImageNet), transfer learning |
| Model runtime | ONNX Runtime 1.26 (CPUExecutionProvider) |
| Backend | FastAPI, Uvicorn, Pillow, python-magic |
| Frontend | Svelte 5, TypeScript, Tailwind CSS |
| Reverse proxy | Caddy 2 |
| Konteneryzacja | Docker Compose |

## Notebook treningowy

[`asl_transfer_learning.ipynb`](asl_transfer_learning.ipynb) uruchamiany w Google Colab realizuje pełny potok:

1. Wczytanie MobileNetV2 lub ResNet18 z wagami ImageNet.
2. Transfer learning na zbiorze [ASL Alphabet (Kaggle)](https://www.kaggle.com/datasets/grassknoted/asl-alphabet) — 400 obrazów na klasę, podział 80/20, 3 epoki.
3. Eksport do ONNX (opset 13, dynamiczny batch).
4. Weryfikacja zgodności predykcji PyTorch vs ONNX Runtime.
5. Pomiar czasu inferencji (PyTorch CPU vs ONNX Runtime CPU).
6. Kwantyzacja statyczna do INT8 (format QDQ, kalibracja na zbiorze walidacyjnym).
7. Pomiar czasu i dokładności modelu INT8 vs FP32.

Po zakończeniu treningu z notebooka pobierane są trzy pliki dla każdego modelu i umieszczane w `backend/modele/<model>/`:

```
backend/modele/
├── mobilenetv2/
│   ├── mobilenetv2_asl.onnx
│   ├── mobilenetv2_asl_int8.onnx
│   └── class_names.json
└── resnet18/
    ├── resnet18_asl.onnx
    ├── resnet18_asl_int8.onnx
    └── class_names.json
```

> **Preprocessing:** obrazy wejściowe są konwertowane przez `RGB -> grayscale -> RGB` (odpowiada sposobowi zbierania zbioru ASL), skalowane do 224x224, a następnie normalizowane statystykami ImageNet (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`). Odbicie poziome jest celowo pominięte — odwróciłoby znaczenie gestu.

## API

Dokumentacja Swagger dostępna pod `/docs` (wyłączona w trybie produkcyjnym, dostępna w dev).

| Endpoint | Opis |
|---|---|
| `POST /predict` | Klasyfikacja obrazu. Parametry: `file` (obraz), `model` (`mobilenetv2`/`resnet18`), `quantized` (bool). Zwraca `predicted`, `confidence`, `top3`. |
| `POST /compare` | Uruchamia wszystkie dostępne warianty (FP32 + INT8) i zwraca tabelę z latencją inferencji. |
| `GET /classes` | Lista klas. |
| `GET /health` | Health check. |

## Uruchomienie

### Wymagania

- Docker i Docker Compose
- Modele ONNX w `backend/modele/` (wygenerowane przez notebook)

### Produkcja

```bash
docker compose up --build
```

Aplikacja dostępna pod `http://localhost`. Backend jest eksponowany wyłącznie wewnątrz sieci Dockera; Caddy kieruje ruch z `/api/*` do backendu i obsługuje TLS.

### Środowisko deweloperskie

```bash
docker compose -f docker-compose.dev.yml up --build
```

W tym trybie backend dostępny jest bezpośrednio pod `http://localhost:8000` (z `/docs`), a frontend pod `http://localhost`.

### Lokalnie bez Dockera

**Backend:**

```bash
cd backend
uv venv && uv pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Struktura projektu

```
.
├── asl_transfer_learning.ipynb   # notebook treningowy (Google Colab)
├── docker-compose.yml            # konfiguracja produkcyjna
├── docker-compose.dev.yml        # konfiguracja deweloperska
├── Caddyfile                     # reverse proxy – produkcja
├── Caddyfile.dev                 # reverse proxy – dev
├── backend/
│   ├── main.py                   # aplikacja FastAPI, lifespan, CORS
│   ├── model.py                  # ładowanie modeli ONNX, preprocessing, inferencja
│   ├── upload.py                 # walidacja i streaming uploadów
│   ├── routes/
│   │   ├── predict.py            # POST /predict, POST /compare
│   │   └── classes.py            # GET /classes
│   ├── modele/                   # pliki .onnx i class_names.json (nie w repo)
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   └── App.svelte            # interfejs użytkownika (upload, wynik, porównanie)
    └── Dockerfile
```

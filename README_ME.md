# Transfer learning + ONNX + kwantyzacja INT8 — Alfabet języka migowego (ASL)

Notebook realizuje punkty **1–7** projektu:
1. Gotowy model (ResNet18 / MobileNetV2, pretrenowany na ImageNet)
2. Transfer learning na zbiorze **ASL Alphabet** (Kaggle) — 29 klas, których ImageNet nie zna
3. Eksport do **ONNX**
4. Sprawdzenie zgodności predykcji PyTorch vs ONNX Runtime
5. Pomiar czasu inferencji (PyTorch CPU, ONNX Runtime CPU)
6. Kwantyzacja do **ONNX INT8**
7. Pomiar czasu modelu skwantyzowanego + porównanie


# tworzenie projektu w dockerze:
## uv

### initialize project
```py
uv init.
```
instalowanie pakietów
```py
uv add fastapi uvicorn[standard] onnxruntime pillow numpy python-multipart aiofiles python-magic
```

ps: python-magic wymaga systemowej biblioteki `libmagic1` stąd w dockerfile `upt-get update`, nie chcesz się bawić? weź `filetypes`

export do requirements
```py
uv export --format requirements-txt > requirements.txt
```

# Docker
zainstaluj na widnowsie, dopal go

pull obrazu
```ps1
docker image pull python:3.12-slim
```

listuj obrazy
```ps1
docker image ls -a
```

Stwórz/kompiluj nasz obraz (-t oznacza TAG)
```ps1
docker build -t asl-backend ./backend
```

odpalasz kontenery z logami
```ps1
docker compose up
```

detach (praca w tle)
```ps1
docker compose up -d
```


## Dockerfile 
to jest to co tworzy nasz obraz

polecam dwa rodzaje obrazów dla małych prijektów `slim` albo `alpine`

Obrazy znajdziesz tutaj, oficialne i customowe -> https://hub.docker.com/_/python

trixie to nazwa debiana jakbyś się zastanawiał
linuxiarze z alpine spuszczają się aby zrobić jak najmniejszy obraz

### Przykład:
```Dockerfile
# Używamy lekkiego obrazu bazowego
FROM python:3.12-slim

# Pobieramy najnowszą wersję 'uv' oficjalnym sposobem
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy najpierw same zależności (dobra praktyka dla cache'owania Dockera)
COPY requirements.txt .

# Instalujemy pakiety systemowo (--system) za pomocą uv
RUN uv pip install --system --no-cache -r requirements.txt

# Kopiujemy resztę kodu (app.py, plik .onnx, class_names.json)
COPY . .

# Wystawiamy port, na którym działa uvicorn
EXPOSE 8000

# Komenda startowa
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```


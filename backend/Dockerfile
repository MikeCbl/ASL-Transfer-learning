# Używamy lekkiego obrazu bazowego
FROM python:3.12.13-slim-trixie

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_LINK_MODE=copy


# libmagic1 -> wymagane przez python-magic
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*



# Pobieramy najnowszą wersję 'uv' oficjalnym sposobem
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Ustawiamy katalog roboczy
WORKDIR /PROJEKT

# Kopiujemy najpierw same zależności (dobra praktyka dla cache'owania Dockera)
COPY requirements.txt .

# 1. Tworzymy wirtualne środowisko wewnątrz obrazu Dockera
ENV VIRTUAL_ENV=/PROJEKT/.venv
RUN uv venv $VIRTUAL_ENV

# 2. Dodajemy je do ścieżki systemowej. Dzięki temu system z automatu
# wie, że wpisanie "python" albo "uvicorn" odnosi się do tego konkretnego środowiska.
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Instalujemy pakiety systemowo (--system) za pomocą uv
# RUN uv pip install --system --no-cache -r requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    HTTP_PROXY="" HTTPS_PROXY="" NO_PROXY="*" \
    uv pip install -r requirements.txt

# Kopiujemy resztę kodu (app.py, plik .onnx, class_names.json)
COPY . .

# Wystawiamy port, na którym działa uvicorn
EXPOSE 8000

# Komenda startowa
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
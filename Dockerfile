# ai-generated: 100% - Generated using Gemini

FROM python:3.13-slim

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie plików zależności i ich instalacja 
# (Wykonujemy to najpierw, aby wykorzystać cache warstw Dockera)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Kopiowanie całego kodu źródłowego aplikacji
COPY src/ /app/src/

# Aplikacja z laboratorium musi nasłuchiwać na porcie 8080
EXPOSE 8080

# Uruchomienie aplikacji używając uvicorn.
# Ponieważ Twój plik to src/main.py, używamy flagi --app-dir /app/src,
# aby wskazać uvicornowi miejsce, w którym ma szukać modułu 'main'.
CMD ["uvicorn", "main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]
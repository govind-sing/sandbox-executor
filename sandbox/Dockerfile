FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    matplotlib \
    pandas \
    numpy \
    pydub \
    reportlab \
    Pillow \
    scipy \
    seaborn

WORKDIR /sandbox

CMD ["python", "-c", "print('sandbox ready')"]
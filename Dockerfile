FROM python:3.12-slim

WORKDIR /app

# 依存ライブラリを先にインストールしてビルドキャッシュを効かせる
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピーする
COPY . .

ENV FLASK_APP=run.py
ENV FLASK_DEBUG=0

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

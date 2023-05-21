FROM python:3.11-slim
LABEL maintainer="David Sn <divad.nnamtdeis@gmail.com>"

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy app files
WORKDIR /app
ADD requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
ADD . ./
CMD ["uvicorn", "mapapylife:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

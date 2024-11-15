
FROM python:3.11-slim-bullseye

ENV HOST=0.0.0.0
 
ENV LISTEN_PORT 8501

RUN apt-get update && rm -rf /var/lib/apt/lists/* && apt-get clean

COPY requirements.txt /app/requirements.txt
 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

WORKDIR /app

COPY demo_app/. .

EXPOSE 8501

CMD ["streamlit", "run", "GP-FSI-Claims-Processing-Initiate-Claim.py", "--server.port", "8501"]


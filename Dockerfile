FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1
LABEL authors="seemyown"

RUN mkdir /organiser_profile_service

WORKDIR /organiser_profile_service

COPY . /organiser_profile_service/

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY .env /organiser_profile_service/

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]



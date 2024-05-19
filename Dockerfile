FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1
LABEL authors="seemyown"

RUN mkdir /user_profile_service

WORKDIR /user_profile_service

COPY . /user_profile_service/

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY .env /user_profile_service/

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]



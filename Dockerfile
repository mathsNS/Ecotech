FROM python:3.12.13-alpine3.24

WORKDIR /usr/src/ecotech

RUN pip install poetry

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . .

CMD [ "python", "run.py" ]
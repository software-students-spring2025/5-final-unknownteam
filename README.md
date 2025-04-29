[![Web App CI](https://github.com/software-students-spring2025/5-final-unknownteam/actions/workflows/web_app.yml/badge.svg)](https://github.com/software-students-spring2025/5-final-unknownteam/actions/workflows/web_app.yml)

## Team Members
[Alex Wang](https://github.com/alw9411), [Melissa Kelly](https://github.com/melissalkelly), [Edwin Chen](https://github.com/Eracks1012), [Wyatt Destabelle](https://github.com/Wyatt-Destabelle)

## Project Description
Our project is a Wordle-esque game where players guess a randomly determined country. Unlike Wordle, however, instead of getting hints about the letters in the name of the country, we give hints on various traits, such as its landmass, GDP, and geographical location.

## Prerequisites

Before starting, ensure you have the following installed:

- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Environment Variables

The following environment variables are required in the `.env` file:

```env
MONGO_URI='mongodb+srv://<username>:<password>@<connectionstring>/<databasename>?ssl=true&ssl_cert_reqs=CERT_NONE'
MONGO_DBNAME=<databasename>
```

## App Setup with Docker

1. Clone the repository:
```python
git clone [repository-url]
cd [repository name]
```

2. Start Docker Compose:
```python
docker-compose down --volumes --remove-orphans
docker-compose up --build
```

3. Access:
- **Web App:** [http://localhost:8080](http://localhost:8080)  
- **MongoDB Express:** [http://localhost:27017](http://localhost:27017)  
  _Login: `admin` / `pass`_

## Container Images
[Web App](https://hub.docker.com/r/mlkelly/5-final-unknownteam-web-app)

## Deployment link
[Play our game!](https://wordle-app-b7yeu.ondigitalocean.app/)

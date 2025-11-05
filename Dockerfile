# should start from `Ubuntu 24.04 LTS` or `python:3.12-slim` image, 
FROM python:3.12-slim
# # install git
RUN apt update && apt install -y git && rm -rf /var/lib/apt/lists/*
# # clone the repo
RUN git clone --depth=1 https://github.com/nav128/the_weather_crew.git
# # set working directory
WORKDIR /the_weather_crew
# pip install it
RUN pip install .

# # optionaly export the security key for the application
# RUN export WEATHER_API_KEY=${WEATHER_API_KEY}
# # Or set it in you host runner variables
# export env var RUN_MODE = REMOTE
RUN export RUN_MODE="REMOTE"
# expose port 8000
EXPOSE 8080

# uv run the api server and on port 8000 
CMD ["uvicorn", "weather.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

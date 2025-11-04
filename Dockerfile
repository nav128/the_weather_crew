# should start from `Ubuntu 24.04 LTS` or `python:3.12-slim` image, 
FROM python:3.12-slim
# install git
RUN apt update && apt install -y git
# clone the repo
RUN git clone https://github.com/nav128/the_weather_crew.git
# set working directory
WORKDIR /the_weather_crew
# pip install it
RUN pip install . --no-cache-dir
# expose port 8000
EXPOSE 8000
# uv run the api server and on port 8000 
CMD ["uv","run", "src/weather/api/main.py", "--port", "8000"]

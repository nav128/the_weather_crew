### run code
#### prerequisits
python 3.12
`git clone --depth=1 https://github.com/nav128/the_weather_crew.git`
`cd the_weather_crew`
`pip install .`
`uvicorn weather.api.main:app`

### or run docker
`docker run -e OPENAI_API_KEY=${OPENAI_API_KEY} -e MODEL=${MODEL} -p 8000:8000 docker.io/batmanmoshe/moshe:crewaish`

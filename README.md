### run code
#### prerequisits
python 3.12\n
#### steps 
- `git clone --depth=1 https://github.com/nav128/the_weather_crew.git`
- `cd the_weather_crew`
- `pip install .`
- `uvicorn weather.api.main:app`

### or run docker

`docker run -e OPENAI_API_KEY=${OPENAI_API_KEY} -e MODEL=${MODEL} -p 8000:8000 docker.io/batmanmoshe/moshe:crewaish`<br/>
replace the provider key as listed in [crewai docs](https://docs.crewai.com/en/concepts/llms#provider-configuration-examples)
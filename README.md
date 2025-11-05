

#### Have your model api key ready
 see option as listed in [crewai docs](https://docs.crewai.com/en/concepts/llms#provider-configuration-examples)
### Run code
#### Prerequisits
python 3.12
#### Steps 
- `git clone --depth=1 https://github.com/nav128/the_weather_crew.git`
- `cd the_weather_crew`
- `pip install .`
- Add .env file in the main folder with `MODEL={MODEL_NAME} {X_API_KEY}={KEY}`
- `uvicorn weather.api.main:app`

### or run docker

`docker run -e OPENAI_API_KEY=${OPENAI_API_KEY} -e MODEL=${MODEL} -p 8000:8000 docker.io/batmanmoshe/moshe:crewaish`<br/>

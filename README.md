

#### Note
Before we start make sure you have an llm model api_key:<br/><t/>
 see option as listed in [crewai docs](https://docs.crewai.com/en/concepts/llms#provider-configuration-examples)

### Run code
#### Prerequisits
python 3.12
#### Steps 
- `git clone --depth=1 https://github.com/nav128/the_weather_crew.git`
- `cd the_weather_crew`
- `pip install .`
- Add .env file in the main folder with `MODEL={MODEL_NAME} {MODEL_API_KEY}={KEY}`
- `uvicorn weather.api.main:app`

### Use docker image
docker image url is `docker.io/batmanmoshe/moshe:crewaish`
#### Run on your machine
`docker run -e OPENAI_API_KEY=${OPENAI_API_KEY} -e MODEL=${MODEL} -p 8080:8080 {DOCKER_IMAGE _URL}`

#### Or deploy on google cloude
create a new service -> 
- make sure memory is 1Gi
- port is 8080
- allow public access from internt
- set env vars:
     - MODEL
   - {MODEL}_API_KEY<br/>
optionaly
    - WEATHER_API_KEY={MAKE UP A SECURIRY CODE}

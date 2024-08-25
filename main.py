import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from langserve import add_routes
from redis import Redis
from starlette.responses import JSONResponse

load_dotenv()

import langchain_chatbot

app = FastAPI()
redis_instance = Redis(host='localhost', port=6379, password='<PASSWORD>', ssl=True)

# /chain/playground
# /chain/invoke
# /chain/stream
# /chain/batch
API_KEY_HEADER = "X-API-KEY"
API_ACCESS_KEY = os.getenv('API_ACCESS_KEY')
API_ACCESS_USER = os.getenv('API_ACCESS_USER')
@app.get("/")
def home_page():
    visits_key = API_ACCESS_KEY # api key
    max_requests = 5
    current_value = redis_instance.get(visits_key)
    if current_value is None:
        redis_instance.set(visits_key, 0, 10)
    redis_instance.incr(visits_key)
    final_value = redis_instance.get(visits_key)
    do_rate_limiting = False
    try:
        do_rate_limiting = int(final_value) > max_requests
    except ValueError:
        pass
    return {"Hello": "World", "visits": final_value, "limited": do_rate_limiting}


@app.middleware("http")
def rate_limit_middleware(request: Request, call_next):
    rate_limit = 5
    rate_window = 10 # seconds
    api_key = request.headers.get(API_KEY_HEADER)
    if api_key is None:
        return JSONResponse(status_code=400, content={"message": "Missing API KEY"})
    if api_key != API_ACCESS_KEY:
        return JSONResponse(status_code=401, content={"message": "Missing API KEY"})
    rate_limit_key = f"rate_limit_{API_ACCESS_USER}"
    access_total_key = f"access_total_{API_ACCESS_USER}"
    rl_current_val = redis_instance.get(rate_limit_key)

    if rl_current_val is None:
        redis_instance.set(rate_limit_key, 0)
    redis_instance.incr(rate_limit_key)
    final_value = redis_instance.get(rate_limit_key)

    do_rate_limiting = False
    try:
        do_rate_limiting = int(final_value) > rate_limit
    except ValueError:
        pass
    if do_rate_limiting:
        return JSONResponse(status_code=429, content={"error": "Rate Limit Exceeded"})

    access_current_val = redis_instance.get(access_total_key)
    if access_current_val is None:
        redis_instance.set(access_total_key, 0, rate_window)
    redis_instance.incr(access_total_key)

    visits_key = API_ACCESS_KEY # api key
    current_value = redis_instance.get(visits_key)
    if current_value is None:
        redis_instance.set(visits_key, 0, rate_window)

    response =  call_next(request)
    return response

chain = langchain_chatbot.get_chain()
add_routes(app, chain, path="/chain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

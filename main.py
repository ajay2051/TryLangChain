import time

import uvicorn
from fastapi import FastAPI, Request
from langserve import add_routes
from redis import Redis
from starlette.responses import JSONResponse

import langchain_chatbot

app = FastAPI()
redis_instance = Redis(host='localhost', port=6379, password='<PASSWORD>', ssl=True)

# /chain/playground
# /chain/invoke
# /chain/stream
# /chain/batch
@app.get("/")
def home_page():
    visits_key = "visits" # api key
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
    visits_key = "visits" # api key
    current_value = redis_instance.get(visits_key)
    if current_value is None:
        redis_instance.set(visits_key, 0, rate_window)
    redis_instance.incr(visits_key)
    final_value = redis_instance.get(visits_key)
    do_rate_limiting = False
    try:
        do_rate_limiting = int(final_value) > rate_limit
    except ValueError:
        pass
    if do_rate_limiting:
        return JSONResponse(status_code=429, content={"error": "Rate Limit Exceeded"})
    response =  call_next(request)
    return response

chain = langchain_chatbot.get_chain()
add_routes(app, chain, path="/chain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

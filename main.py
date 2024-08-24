import uvicorn
from fastapi import FastAPI
from langserve import add_routes

import langchain_chatbot

app = FastAPI()


# /chain/playground
# /chain/invoke
# /chain/stream
# /chain/batch
@app.get("/")
def home_page():
    return {"Hello": "World"}


chain = langchain_chatbot.get_chain()
add_routes(app, chain, path="/chain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

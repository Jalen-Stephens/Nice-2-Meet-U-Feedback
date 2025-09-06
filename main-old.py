from fastapi import FastAPI
import uvicorn

from datetime import datetime
import socket
from typing import Optional
from fastapi import Query, Path

from models.health import Health

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

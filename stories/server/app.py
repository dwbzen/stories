import uvicorn

if __name__ == "__main__":
    uvicorn.run("server:app", port=9000, reload=True)
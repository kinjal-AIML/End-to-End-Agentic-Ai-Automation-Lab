from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="n8n API",
    description="API for interacting with n8n workflows"
)

@app.get("/health")
def health_check():
    return {"status": "healthy and system is working"}

@app.get("/status")
def status_check():
    return {"status": "n8n API is running smoothly"}

@app.get("/")
def root():
    return {"message": "Welcome to the n8n API"}


@app.get("/facts")
def get_facts():
    return {"messages": ["n8n is an open-source workflow automation tool.", "It allows you to connect different apps and services.", "You can create complex workflows without coding."]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
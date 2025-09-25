from fastapi import FastAPI

async def test_func():
    print("Project will be start on Tomorrow")


app = FastAPI(
    title="Test Line Api",
    description="Test line Endpoint",
    version="1.0.1"
)
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_func())
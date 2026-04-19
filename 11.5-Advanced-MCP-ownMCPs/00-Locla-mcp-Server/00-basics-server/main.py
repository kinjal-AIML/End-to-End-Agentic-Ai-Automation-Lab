import random
from fastmcp import FastMCP

mcp = FastMCP(name="Local Demo Server")

@mcp.tool
def roll_dice(n_dice: int = 1) -> list[int]:
    """Roll a specified number of dice and return the results."""
    return [random.randint(1, 6) for _ in range(n_dice)]


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b


if __name__ == "__main__":
    mcp.run()
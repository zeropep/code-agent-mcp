import asyncio
import sys
from src.api_client import FastAPIClient

async def test():
    try:
        # Test API connection
        print("Testing API connection...", file=sys.stderr)
        client = FastAPIClient(base_url="http://localhost:8000")
        result = await client.list_projects()
        print(f"Projects: {result}", file=sys.stderr)
        await client.close()
        print("SUCCESS", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())

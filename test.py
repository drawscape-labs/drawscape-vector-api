import asyncio
import aiohttp
import time
import subprocess
import os
import psutil

def log_memory_usage():
    # Get process memory info
    print(os.getpid())
    process = psutil.Process(os.getpid())
    
    # Get memory info in bytes and convert to MB
    memory_info = process.memory_info()
    memory_usage_mb = memory_info.rss / (1024 * 1024)
    
    print(f"Memory usage: {memory_usage_mb:.2f} MB")

async def make_request(session, url):
    async with session.get(url) as response:
        await response.text()
        return response.status

async def run_test(url, num_requests, concurrency):

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrency)
        tasks = []

        async def bounded_request():
            async with semaphore:
                return await make_request(session, url)

        for _ in range(num_requests):
            task = asyncio.ensure_future(bounded_request())
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

    total_time = end_time - start_time
    success_count = responses.count(200)

    log_memory_usage()
    
    print(f"Total requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print(f"Successful requests: {success_count}")
    print(f"Failed requests: {num_requests - success_count}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Requests per second: {num_requests / total_time:.2f}")


# asyncio.run(run_test('https://drawscape-api-test-8af41b194ec8.herokuapp.com/factorio/render-project/491f026b-3fc7-4cea-8392-4980378bc408?theme_name=squares&color_scheme=black', 1, 1))
asyncio.run(run_test('https://drawscape-api-test-8af41b194ec8.herokuapp.com/', 100, 11))
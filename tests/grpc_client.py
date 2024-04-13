import json
import os
import grpc
import concurrent.futures
import random
import time  # Import the time module
from price_tag_analyzer.grpc_compiled import PriceTagAnalyzerService_pb2, PriceTagAnalyzerService_pb2_grpc


def send_request():
    start_time = time.time()  # Start time for this request

    channel = grpc.insecure_channel('5.35.11.158:50051')
    # channel = grpc.insecure_channel('localhost:50051')
    stub = PriceTagAnalyzerService_pb2_grpc.PriceTagAnalyzerServiceStub(channel)

    def generate_chunks(image_path):
        with open(image_path, "rb") as image_file:
            while chunk := image_file.read(1024 * 1024):
                yield PriceTagAnalyzerService_pb2.ImageChunk(content=chunk)

    try:
        image_dir = './test_images'
        image_files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
        random_image = random.choice(image_files)
        image_path = os.path.join(image_dir, random_image)

        response = stub.AnalyzeImage(generate_chunks(image_path))
        print("Image info received:", response)
    except grpc.RpcError as e:
        print(f"RPC failed with status code {e.code()}: {e.details()}")
        print(json.loads(e.details()))
    finally:
        end_time = time.time()  # End time for this request
        print(f"Request took {end_time - start_time} seconds.")


if __name__ == '__main__':
    num_requests = 20  # Change this to the number of requests you want to send

    overall_start_time = time.time()  # Start time for all requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(send_request) for _ in range(num_requests)]
        concurrent.futures.wait(futures)
    overall_end_time = time.time()  # End time for all requests
    print(f"All requests completed in {overall_end_time - overall_start_time} seconds.")

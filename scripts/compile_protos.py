import os
import shutil
import subprocess


def setup_directories():
    # Create necessary directories
    os.makedirs('proto/price_tag_analyzer/grpc_compiled', exist_ok=True)
    # Copy .proto files
    shutil.copy(
        '../proto/PriceTagAnalyzerService.proto',
        'proto/price_tag_analyzer/grpc_compiled/PriceTagAnalyzerService.proto'
    )


def generate_protos():
    # Generate GRPC code for server
    subprocess.run([
        'python', '-m', 'grpc_tools.protoc',
        '--proto_path=./proto/',
        '--python_out=.',
        '--grpc_python_out=.',
        '--pyi_out=.',
        'price_tag_analyzer/grpc_compiled/PriceTagAnalyzerService.proto'
    ], check=True)


def cleanup():
    # Remove temporary directories
    shutil.rmtree('proto/price_tag_analyzer', ignore_errors=True)


def main():
    print("[1/3] Copying files...")
    setup_directories()

    print("[2/3] Generating proto...")
    generate_protos()

    print("[3/3] Removing files...")
    cleanup()

    print("Completed!")


if __name__ == "__main__":
    main()

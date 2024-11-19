import shutil
import subprocess

from pathlib import Path


def generate_client():
    # Remove existing graphql_client directory
    client_dir = Path("src/synmetrix_python_client/graphql_client")
    if client_dir.exists():
        shutil.rmtree(client_dir)

    # Run ariadne-codegen
    subprocess.run(["ariadne-codegen"], check=True)

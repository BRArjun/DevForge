import docker
import os
import tempfile
import subprocess
import pty
import select
import fcntl
import termios
import struct
import signal
from typing import Callable
from queue import Queue

class DockerPythonRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python-runner"
        self.container_name = "python-container"
        
    def build_docker_image(self, directory_path):
        dockerfile_content = '''
FROM python:3.9
WORKDIR /app
COPY . /app
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            try:
                self.client.images.build(path=directory_path, dockerfile=dockerfile_path, tag=self.image_name)
                return True
            except docker.errors.BuildError as e:
                print(f"Build error: {e}")
                return False

    def run_interactive_python(self, directory_path: str, main_file: str, 
                               output_callback: Callable[[str], None],
                               input_queue: Queue):
        """
        Run Python script with interactive I/O support
        
        Args:
            directory_path: Path to the directory containing all Python files
            main_file: Name of the main Python file to run
            output_callback: Callback function to handle program output
            input_queue: Queue to receive input from the user
        """
        if not os.path.exists(os.path.join(directory_path, main_file)):
            raise FileNotFoundError(f"File {main_file} does not exist in the specified directory")
        
        try:
            # Build the Docker image
            if not self.build_docker_image(directory_path):
                raise RuntimeError("Failed to build Docker image")

            # Cleanup any existing container
            try:
                old_container = self.client.containers.get(self.container_name)
                old_container.stop()
                old_container.remove()
            except docker.errors.NotFound:
                pass
            
            # Create new container with TTY
            container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                command="tail -f /dev/null",
                detach=True,
                tty=True,
                stdin_open=True
            )
            
            try:
                # Create exec instance with TTY
                exec_id = container.client.api.exec_create(
                    container.id,
                    f'python /app/{main_file}',
                    tty=True,
                    stdin=True
                )
                
                # Start the exec instance
                socket = container.client.api.exec_start(
                    exec_id,
                    socket=True,
                    tty=True
                )
                
                # Set socket to non-blocking mode
                socket._sock.setblocking(False)
                
                while True:
                    # Check for program output
                    try:
                        output = socket._sock.recv(4096)
                        if output:
                            decoded_output = output.decode('utf-8', errors='replace')
                            output_callback(decoded_output)
                    except (BlockingIOError, docker.errors.APIError):
                        pass
                    
                    # Check for user input
                    try:
                        user_input = input_queue.get_nowait()
                        if user_input:
                            socket._sock.send(user_input.encode() + b'\n')
                    except Exception:
                        pass
                    
                    # Check if program has finished
                    inspect = container.client.api.exec_inspect(exec_id)
                    if inspect['ExitCode'] is not None:
                        break
                        
            finally:
                container.stop()
                container.remove()
                
        except Exception as e:
            raise RuntimeError(f"Container error: {e}")

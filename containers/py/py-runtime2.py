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

class DockerPythonRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python-runner"
        self.container_name = "python-container"
        
    def build_docker_image(self, requirements=None):
        dockerfile_content = '''
FROM python:3.9
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            requirements_path = os.path.join(tmpdir, 'requirements.txt')
            
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            with open(requirements_path, 'w') as f:
                if requirements:
                    f.write('\n'.join(requirements))
                else:
                    f.write('# No additional requirements')
            
            try:
                self.client.images.build(path=tmpdir, tag=self.image_name)
                return True
            except docker.errors.BuildError as e:
                return False

    def run_interactive_python(self, python_file_path: str, 
                             output_callback: Callable[[str], None],
                             input_queue: "Queue"):
        """
        Run Python script with interactive I/O support
        
        Args:
            python_file_path: Path to the Python file to run
            output_callback: Callback function to handle program output
            input_queue: Queue to receive input from the user
        """
        if not os.path.exists(python_file_path):
            raise FileNotFoundError(f"File {python_file_path} does not exist")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            python_file_name = os.path.basename(python_file_path)
            temp_python_file = os.path.join(tmpdir, python_file_name)
            subprocess.run(['cp', python_file_path, temp_python_file])
            
            try:
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
                    volumes={tmpdir: {'bind': '/app', 'mode': 'rw'}},
                    detach=True,
                    tty=True,
                    stdin_open=True
                )
                
                try:
                    # Create exec instance with TTY
                    exec_id = container.client.api.exec_create(
                        container.id,
                        f'python /app/{python_file_name}',
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

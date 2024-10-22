# import docker
# import os
# import tempfile
# import subprocess
# import pty
# import select
# import fcntl
# import termios
# import struct
# import signal
# from typing import Callable
# from queue import Queue
# import logging
# import time

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)


# class DockerPythonRunner:
#     def __init__(self):
#         self.client = docker.from_env()
#         self.image_name = "python-runner"
#         self.container_name = "python-container"
        
#     def build_docker_image(self, directory_path):
#         dockerfile_content = '''
# FROM python:3.9
# WORKDIR /app
# COPY . /app/
# '''
#         with tempfile.TemporaryDirectory() as tmpdir:
#             dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            
#             with open(dockerfile_path, 'w') as f:
#                 f.write(dockerfile_content)
            
#             try:
#                 self.client.images.build(path=directory_path, dockerfile=dockerfile_path, tag=self.image_name)
#                 return True
#             except docker.errors.BuildError as e:
#                 print(f"Build error: {e}")
#                 return False

#     def run_interactive_python(self, directory_path: str, main_file: str, 
#                                output_callback: Callable[[str], None],
#                                input_queue: Queue):
#         """
#         Run Python script with interactive I/O support
        
#         Args:
#             directory_path: Path to the directory containing all Python files
#             main_file: Name of the main Python file to run
#             output_callback: Callback function to handle program output
#             input_queue: Queue to receive input from the user
#         """
#         if not os.path.exists(os.path.join(directory_path, main_file)):
#             raise FileNotFoundError(f"File {main_file} does not exist in the specified directory")
        
#         try:
#             # Build the Docker image
#             if not self.build_docker_image(directory_path):
#                 raise RuntimeError("Failed to build Docker image")

#             # Cleanup any existing container
#             try:
#                 old_container = self.client.containers.get(self.container_name)
#                 old_container.stop()
#                 old_container.remove()
#             except docker.errors.NotFound:
#                 pass
            
#             # Create new container with TTY
#             container = self.client.containers.run(
#                 self.image_name,
#                 name=self.container_name,
#                 command="tail -f /dev/null",
#                 detach=True,
#                 tty=True,
#                 stdin_open=True
#             )
            
#             try:
#                 # Create exec instance with TTY
#                 exec_id = container.client.api.exec_create(
#                     container.id,
#                     f'python /app/{main_file}',
#                     tty=True,
#                     stdin=True
#                 )
                
#                 # Start the exec instance
#                 socket = container.client.api.exec_start(
#                     exec_id,
#                     socket=True,
#                     tty=True
#                 )
                
#                 # Set socket to non-blocking mode
#                 socket._sock.setblocking(False)
                
#                 while True:
#                     # Check for program output
#                     try:
#                         output = socket._sock.recv(4096)
#                         if output:
#                             decoded_output = output.decode('utf-8', errors='replace')
#                             output_callback(decoded_output)
#                     except (BlockingIOError, docker.errors.APIError):
#                         pass
                    
#                     # Check for user input
#                     try:
#                         user_input = input_queue.get_nowait()
#                         if user_input:
#                             socket._sock.send(user_input.encode() + b'\n')
#                     except Exception:
#                         pass
                    
#                     # Check if program has finished
#                     inspect = container.client.api.exec_inspect(exec_id)
#                     if inspect['ExitCode'] is not None:
#                         break
                        
#             finally:
#                 container.stop()
#                 container.remove()
                
#         except Exception as e:
#             raise RuntimeError(f"Container error: {e}")


#     def execute_command(self, project_dir, command, file_structure):
#         try:
#             logger.info(f"Executing command: {command}")
#             logger.info(f"Project directory: {project_dir}")
#             logger.info(f"File structure: {file_structure}")

#             self._remove_existing_container()
        
#             # Create file structure in the project directory
#             self._create_file_structure(project_dir, file_structure)

#             # Log the contents of the project directory
#             logger.info(f"Contents of {project_dir}:")
#             for root, dirs, files in os.walk(project_dir):
#                 for file in files:
#                     logger.info(os.path.join(root, file))

#             # Create a shell script to run the command and capture output
#             script_content = f"""#!/bin/bash
# cd /app
# {command} 2>&1 | tee /app/output.log
# echo $? > /app/exit_code.txt
# """
#             script_path = os.path.join(project_dir, 'run_command.sh')
#             with open(script_path, 'w') as f:
#                 f.write(script_content)
#             os.chmod(script_path, 0o755)

#             container = self.client.containers.run(
#                 self.image_name,
#                 name=self.container_name,
#                 command=["/app/run_command.sh"],
#                 volumes={project_dir: {'bind': '/app', 'mode': 'rw'}},
#                 working_dir='/app',
#                 detach=True,
#                 tty=True,
#                 stdin_open=True,
#             )
#             logger.info(f"Container created with ID: {container.id}")
#             return container.id
#         except Exception as e:
#             logger.error(f"Error in execute_command: {e}")
#             return None 

#     def _create_file_structure(self, base_dir, file_structure):
#         for item in file_structure:
#             path = os.path.join(base_dir, item['path'])
#             if item['type'] == 'directory':
#                 os.makedirs(path, exist_ok=True)
#             elif item['type'] == 'file':
#                 os.makedirs(os.path.dirname(path), exist_ok=True)
#                 with open(path, 'w') as f:
#                     f.write(item['content'])


#     def install_package(self, package_name):
#         try:
#             self._remove_existing_container()
            
#             container = self.client.containers.run(
#                 self.image_name,
#                 name=self.container_name,
#                 command=f"pip install {package_name}",
#                 detach=True,
#                 tty=True,
#                 stdin_open=True,
#             )
            
#             return container.id
#         except docker.errors.ContainerError as e:
#             return f"Container error: {e}"
#         except docker.errors.ImageNotFound:
#             return f"Image {self.image_name} not found"

#     def _remove_existing_container(self):
#         try:
#             old_container = self.client.containers.get(self.container_name)
#             old_container.stop()
#             old_container.remove()
#         except docker.errors.NotFound:
#             pass

#     def get_container_output(self, container_id):
#         if not container_id:
#             yield "Failed to create container"
#             return

#         try:
#             container = self.client.containers.get(container_id)
            
#             # Wait for container to start
#             time.sleep(1)
            
#             while container.status == 'running':
#                 container.reload()
                
#                 try:
#                     # Read the current content of the output file
#                     output = container.exec_run("cat /app/output.log")
#                     if output.exit_code == 0:
#                         lines = output.output.decode('utf-8').splitlines()
#                         for line in lines:
#                             logger.info(f"Container output: {line}")
#                             yield line
#                 except docker.errors.APIError as e:
#                     logger.error(f"Error reading container output: {e}")
                    
#                 time.sleep(0.1)
            
#             # Read final output and exit code
#             try:
#                 output = container.exec_run("cat /app/output.log")
#                 exit_code = container.exec_run("cat /app/exit_code.txt")
                
#                 if output.exit_code == 0:
#                     lines = output.output.decode('utf-8').splitlines()
#                     for line in lines:
#                         logger.info(f"Container output: {line}")
#                         yield line
                
#                 if exit_code.exit_code == 0:
#                     exit_code_value = int(exit_code.output.decode('utf-8').strip())
#                     logger.info(f"Container exit code: {exit_code_value}")
#                     yield f"Container has finished execution with exit code: {exit_code_value}"
                    
#                     if exit_code_value != 0:
#                         error_logs = container.logs(stdout=False, stderr=True)
#                         logger.error(f"Container error logs: {error_logs.decode('utf-8')}")
#                         yield f"Error occurred: {error_logs.decode('utf-8')}"
#             except docker.errors.APIError as e:
#                 logger.error(f"Error reading final output: {e}")
#                 yield f"Error reading final output: {e}"
                
#         except docker.errors.NotFound:
#             logger.error(f"Container not found: {container_id}")
#             yield "Container not found"
#         except Exception as e:
#             logger.error(f"Error getting container output: {e}")
#             yield f"Error getting container output: {e}"
#         finally:
#             try:
#                 container.remove(force=True)
#             except Exception as e:
#                 logger.error(f"Error removing container: {e}")

#     def send_input_to_container(self, container_id, input_data):
#         try:
#             container = self.client.containers.get(container_id)
#             sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
#             sock._sock.send(input_data.encode() + b'\n')
#             return True
#         except docker.errors.NotFound:
#             return False

#     def send_interactive_input(self, container_id, input_data):
#         try:
#             container = self.client.containers.get(container_id)
#             sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
#             sock._sock.send(input_data.encode() + b'\n')
#             return True
#         except docker.errors.NotFound:
#             return False

# def main():
#     runner = DockerPythonRunner()
#     if not runner.build_docker_image():
#         return

# if __name__ == "__main__":
#     main()




# import docker
# import os
# import tempfile
# import subprocess
# import pty
# import select
# import fcntl
# import termios
# import struct
# import signal
# import time
# from typing import Callable
# from queue import Queue
# import logging

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# class DockerPythonRunner:
#     def __init__(self):
#         self.client = docker.from_env()
#         self.image_name = "python-runner"
#         self.container_name = "python-container"
        
#     def build_docker_image(self, directory_path):
#         dockerfile_content = '''
# FROM python:3.9
# WORKDIR /app
# COPY . /app/
# '''
#         with tempfile.TemporaryDirectory() as tmpdir:
#             dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            
#             with open(dockerfile_path, 'w') as f:
#                 f.write(dockerfile_content)
            
#             try:
#                 self.client.images.build(path=directory_path, dockerfile=dockerfile_path, tag=self.image_name)
#                 return True
#             except docker.errors.BuildError as e:
#                 logger.error(f"Build error: {e}")
#                 return False

#     def execute_command(self, project_dir, command, file_structure):
#         try:
#             logger.info(f"Executing command: {command}")
#             logger.info(f"Project directory: {project_dir}")
#             logger.info(f"File structure: {file_structure}")

#             self._remove_existing_container()
        
#             # Create file structure in the project directory
#             self._create_file_structure(project_dir, file_structure)

#             # Build image with the project files
#             if not self.build_docker_image(project_dir):
#                 raise RuntimeError("Failed to build Docker image")

#             # Create a shell script to run the command
#             script_content = f"""#!/bin/bash
# cd /app
# {command}
# """
#             script_path = os.path.join(project_dir, 'run_command.sh')
#             with open(script_path, 'w') as f:
#                 f.write(script_content)
#             os.chmod(script_path, 0o755)

#             # Run the container with command output directly to logs
#             container = self.client.containers.run(
#                 self.image_name,
#                 name=self.container_name,
#                 command=["/bin/bash", "/app/run_command.sh"],
#                 volumes={project_dir: {'bind': '/app', 'mode': 'rw'}},
#                 working_dir='/app',
#                 detach=True,
#                 tty=True,
#                 stdin_open=True
#             )
#             logger.info(f"Container created with ID: {container.id}")
#             return container.id
#         except Exception as e:
#             logger.error(f"Error in execute_command: {e}")
#             return None

#     def get_container_output(self, container_id):
#         if not container_id:
#             yield "Failed to create container"
#             return

#         try:
#             container = self.client.containers.get(container_id)
            
#             # Get initial logs
#             logs = container.logs(stdout=True, stderr=True, stream=True, follow=True)
            
#             # Stream logs while container is running
#             for line in logs:
#                 try:
#                     decoded_line = line.decode('utf-8').strip()
#                     if decoded_line:
#                         logger.info(f"Container output: {decoded_line}")
#                         yield decoded_line
#                 except UnicodeDecodeError:
#                     continue
                
#             # Get final status
#             container.reload()
#             exit_code = container.attrs['State']['ExitCode']
            
#             yield f"\nContainer finished with exit code: {exit_code}"
            
#             if exit_code != 0:
#                 error_logs = container.logs(stdout=False, stderr=True)
#                 error_message = error_logs.decode('utf-8').strip()
#                 if error_message:
#                     yield f"\nError output:\n{error_message}"
                    
#         except docker.errors.NotFound:
#             logger.error(f"Container not found: {container_id}")
#             yield "Container not found"
#         except Exception as e:
#             logger.error(f"Error getting container output: {e}")
#             yield f"Error getting container output: {e}"
#         finally:
#             try:
#                 # Clean up the container
#                 container = self.client.containers.get(container_id)
#                 container.remove(force=True)
#             except docker.errors.NotFound:
#                 pass
#             except Exception as e:
#                 logger.error(f"Error removing container: {e}")

#     def _create_file_structure(self, base_dir, file_structure):
#         for item in file_structure:
#             path = os.path.join(base_dir, item['path'])
#             if item['type'] == 'directory':
#                 os.makedirs(path, exist_ok=True)
#             elif item['type'] == 'file':
#                 os.makedirs(os.path.dirname(path), exist_ok=True)
#                 with open(path, 'w') as f:
#                     f.write(item['content'])

#     def _remove_existing_container(self):
#         try:
#             old_container = self.client.containers.get(self.container_name)
#             old_container.remove(force=True)
#         except docker.errors.NotFound:
#             pass
#         except Exception as e:
#             logger.error(f"Error removing existing container: {e}")

#     def send_input_to_container(self, container_id, input_data):
#         try:
#             container = self.client.containers.get(container_id)
#             if container.status == 'running':
#                 sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
#                 sock._sock.send(input_data.encode() + b'\n')
#                 return True
#             return False
#         except docker.errors.NotFound:
#             return False
#         except Exception as e:
#             logger.error(f"Error sending input to container: {e}")
#             return False




import docker
import os
import tempfile
import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DockerPythonRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python-runner"
        self.container_name = "python-container"
        self.project_dir = tempfile.mkdtemp()
        logger.debug(f"Project directory created: {self.project_dir}")
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM python:3.9
WORKDIR /app
CMD ["tail", "-f", "/dev/null"]
'''
        dockerfile_path = os.path.join(self.project_dir, 'Dockerfile')
        
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        try:
            self.client.images.build(path=self.project_dir, dockerfile=dockerfile_path, tag=self.image_name)
            logger.debug(f"Docker image built successfully: {self.image_name}")
            return True
        except docker.errors.BuildError as e:
            logger.error(f"Build error: {e}")
            return False

    def create_file(self, file_path, content):
        full_path = os.path.join(self.project_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        logger.debug(f"Created file: {full_path}")
        logger.debug(f"File content: {content}")
    
        # Add this to check if the file was actually created
        if os.path.exists(full_path):
            logger.debug(f"File {full_path} was successfully created")
        else:
            logger.error(f"Failed to create file {full_path}")

    def execute_command(self, command):
        container = None
        try:
            logger.debug(f"Executing command: {command}")
            logger.debug(f"Project directory contents:")
            for root, dirs, files in os.walk(self.project_dir):
                for file in files:
                    logger.debug(os.path.join(root, file))

            self._remove_existing_container()
    
            # Build image if it doesn't exist
            if self.image_name not in [img.tags for img in self.client.images.list()]:
                if not self.build_docker_image():
                    raise RuntimeError("Failed to build Docker image")

        # Run the container
            container = self.client.containers.run(
                self.image_name,
                name=self.container_name,
                volumes={self.project_dir: {'bind': '/app', 'mode': 'rw'}},
                working_dir='/app',
                detach=True,
                tty=True,
                stdin_open=True
            )
            logger.debug(f"Container created with ID: {container.id}")

            # Check container's /app directory
            exec_result = container.exec_run("ls -la /app")
            logger.debug(f"Contents of container's /app directory: {exec_result.output.decode('utf-8')}")

            # Execute command in running container
            exec_result = container.exec_run(f"/bin/bash -c '{command}'", stream=True)
            for output in exec_result.output:
                yield output.decode('utf-8').strip()
            # Get exit code
            exit_code = exec_result.exit_code
            yield f"\nCommand finished with exit code: {exit_code}"

            if exit_code != 0:
                # If there was an error, log the container filesystem
                logger.debug("Container filesystem:")
                fs_result = container.exec_run("find /app -type f")
                fs_output = fs_result.output.decode('utf-8')
                logger.debug(fs_output)
                yield f"\nContainer filesystem:\n{fs_output}"

            return container.id
        except Exception as e:
            logger.error(f"Error in execute_command: {e}")
            yield f"Error in execute_command: {str(e)}"
            return None
        finally:
            if container:
                container.stop()
                container.remove()
                logger.debug(f"Container {container.id} stopped and removed")

    def _remove_existing_container(self):
        try:
            old_container = self.client.containers.get(self.container_name)
            old_container.remove(force=True)
            logger.debug(f"Removed existing container: {self.container_name}")
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error removing existing container: {e}")

    def send_input_to_container(self, container_id, input_data):
        try:
            container = self.client.containers.get(container_id)
            if container.status == 'running':
                sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
                sock._sock.send(input_data.encode() + b'\n')
                logger.debug(f"Input sent to container: {input_data}")
                return True
            return False
        except docker.errors.NotFound:
            return False
        except Exception as e:
            logger.error(f"Error sending input to container: {e}")
            return False

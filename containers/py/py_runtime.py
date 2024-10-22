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

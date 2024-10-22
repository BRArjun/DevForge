import docker
import os
import tempfile
import subprocess

class DockerPythonRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python-runner"
        self.container_name = "python-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM python:3.9
WORKDIR /app
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            try:
                self.client.images.build(path=tmpdir, tag=self.image_name)
                print("Docker image built successfully")
            except docker.errors.BuildError as e:
                print(f"Failed to build Docker image: {e}")
                return False
        return True

    def run_python_script(self, python_file_path):
        if not os.path.exists(python_file_path):
            print(f"Error: File {python_file_path} does not exist")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            python_file_name = os.path.basename(python_file_path)
            temp_python_file = os.path.join(tmpdir, python_file_name)
            subprocess.run(['cp', python_file_path, temp_python_file])

            try:
                # Remove existing container if it exists
                try:
                    old_container = self.client.containers.get(self.container_name)
                    old_container.stop()
                    old_container.remove()
                except docker.errors.NotFound:
                    pass

                # Create and start container
                container = self.client.containers.run(
                    self.image_name,
                    name=self.container_name,
                    command="tail -f /dev/null",
                    volumes={tmpdir: {'bind': '/app', 'mode': 'rw'}},
                    detach=True,
                )

                try:
                    # Run the Python script interactively
                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        'python', f'/app/{python_file_name}'
                    ])

                finally:
                    # Cleanup
                    container.stop()
                    container.remove()

            except docker.errors.ContainerError as e:
                print(f"Container error: {e}")
            except docker.errors.ImageNotFound:
                print(f"Image {self.image_name} not found")

def main():
    runner = DockerPythonRunner()
    
    # Build Docker image
    if not runner.build_docker_image():
        return

    # Get Python file path from user
    python_file_path = input("Enter the path to your Python file: ")
    
    # Run the Python program
    runner.run_python_script(python_file_path)

if __name__ == "__main__":
    main()

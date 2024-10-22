import docker
import os
import tempfile
import subprocess

class DockerPythonRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "python-runner"
        self.container_name = "python-container"
        
    def build_docker_image(self, requirements=None):
        dockerfile_content = '''
FROM python:3.9-slim
WORKDIR /app
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
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
                try:
                    old_container = self.client.containers.get(self.container_name)
                    old_container.stop()
                    old_container.remove()
                except docker.errors.NotFound:
                    pass
                
                container = self.client.containers.run(
                    self.image_name,
                    name=self.container_name,
                    command="tail -f /dev/null",
                    volumes={tmpdir: {'bind': '/app', 'mode': 'rw'}},
                    detach=True,
                )
                
                try:
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

    def execute_command(self, command):
        try:
            container = self.client.containers.get(self.container_name)
            result = container.exec_run(command)
            return result.output.decode('utf-8')
        except docker.errors.NotFound:
            return "Container not found. Please run a Python script first."
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    runner = DockerPythonRunner()
    
    requirements = input("Enter required packages (comma-separated) or press Enter for none: ").strip()
    requirements_list = [req.strip() for req in requirements.split(',')] if requirements else None
    
    if not runner.build_docker_image(requirements_list):
        return
    
    python_file_path = input("Enter the path to your Python file: ")
    
    runner.run_python_script(python_file_path)

if __name__ == "__main__":
    main()

import docker
import os
import tempfile
import subprocess

class DockerCRunner:
    def __init__(self):
        self.client = docker.from_env()  # Fixed: Changed from docker.from_client()
        self.image_name = "gcc-runner"
        self.container_name = "gcc-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM gcc:latest
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

    def compile_and_run(self, c_file_path):
        if not os.path.exists(c_file_path):
            print(f"Error: File {c_file_path} does not exist")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            c_file_name = os.path.basename(c_file_path)
            temp_c_file = os.path.join(tmpdir, c_file_name)
            subprocess.run(['cp', c_file_path, temp_c_file])

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
                    command="tail -f /dev/null",  # Keep container running
                    volumes={tmpdir: {'bind': '/app', 'mode': 'rw'}},
                    detach=True,
                )

                try:
                    exec_result = container.exec_run(
                        f"gcc -o /app/program /app/{c_file_name}"
                    )
                    if exec_result.exit_code != 0:
                        print("Compilation failed:")
                        print(exec_result.output.decode())
                        return

                    print("Program compiled successfully")

                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        '/app/program'
                    ])

                finally:
                    container.stop()
                    container.remove()

            except docker.errors.ContainerError as e:
                print(f"Container error: {e}")
            except docker.errors.ImageNotFound:
                print(f"Image {self.image_name} not found")

def main():
    runner = DockerCRunner()
    
    if not runner.build_docker_image():
        return

    c_file_path = input("Enter the path to your C file: ")
    
    runner.compile_and_run(c_file_path)

if __name__ == "__main__":
    main()

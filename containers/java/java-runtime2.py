import docker
import os
import tempfile
import subprocess

class DockerJavaRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "java-runner"
        self.container_name = "java-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM openjdk:11
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

    def compile_and_run(self, java_file_path):
        if not os.path.exists(java_file_path):
            print(f"Error: File {java_file_path} does not exist")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            java_file_name = os.path.basename(java_file_path)
            temp_java_file = os.path.join(tmpdir, java_file_name)
            subprocess.run(['cp', java_file_path, temp_java_file])

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
                    # Compile the Java file
                    exec_result = container.exec_run(
                        f"javac /app/{java_file_name}"
                    )
                    if exec_result.exit_code != 0:
                        print("Compilation failed:")
                        print(exec_result.output.decode())
                        return

                    print("Program compiled successfully")

                    # Extract class name from file name (assuming it matches)
                    class_name = os.path.splitext(java_file_name)[0]

                    # Run the program interactively
                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        'java', '-cp', '/app', class_name
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
    runner = DockerJavaRunner()
    
    # Build Docker image
    if not runner.build_docker_image():
        return

    # Get Java file path from user
    java_file_path = input("Enter the path to your Java file: ")
    
    # Compile and run the Java program
    runner.compile_and_run(java_file_path)

if __name__ == "__main__":
    main()

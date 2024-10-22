import docker
import os
import tempfile
import subprocess

class DockerGoRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "go-runner"
        self.container_name = "go-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM golang:1.20
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

    def run_go_program(self, go_file_path):
        if not os.path.exists(go_file_path):
            print(f"Error: File {go_file_path} does not exist")
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            go_file_name = os.path.basename(go_file_path)
            temp_go_file = os.path.join(tmpdir, go_file_name)
            
            subprocess.run(['cp', go_file_path, temp_go_file])
            go_mod_path = os.path.join(os.path.dirname(go_file_path), 'go.mod')
            if os.path.exists(go_mod_path):
                subprocess.run(['cp', go_mod_path, os.path.join(tmpdir, 'go.mod')])
            
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
                    if not os.path.exists(go_mod_path):
                        init_result = container.exec_run("go mod init temp")
                        if init_result.exit_code != 0:
                            print("Failed to initialize Go module:")
                            print(init_result.output.decode())
                            return
                    
                    tidy_result = container.exec_run("go mod tidy")
                    if tidy_result.exit_code != 0:
                        print("Failed to download dependencies:")
                        print(tidy_result.output.decode())
                        return
                    
                    build_result = container.exec_run(f"go build -o program {go_file_name}")
                    if build_result.exit_code != 0:
                        print("Build failed:")
                        print(build_result.output.decode())
                        return
                    
                    print("Program built successfully")
                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        '/app/program'
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
    runner = DockerGoRunner()
    
    if not runner.build_docker_image():
        return
    
    go_file_path = input("Enter the path to your Go file: ")
    
    runner.run_go_program(go_file_path)

if __name__ == "__main__":
    main()

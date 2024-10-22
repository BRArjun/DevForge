import docker
import os
import tempfile
import subprocess

class DockerJavaScriptRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "js-runner"
        self.container_name = "js-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM node:16
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

    def run_javascript(self, js_file_path):
        if not os.path.exists(js_file_path):
            print(f"Error: File {js_file_path} does not exist")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            js_file_name = os.path.basename(js_file_path)
            temp_js_file = os.path.join(tmpdir, js_file_name)
            
            subprocess.run(['cp', js_file_path, temp_js_file])
            package_json_path = os.path.join(os.path.dirname(js_file_path), 'package.json')
            if os.path.exists(package_json_path):
                subprocess.run(['cp', package_json_path, os.path.join(tmpdir, 'package.json')])

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
                    if os.path.exists(package_json_path):
                        install_result = container.exec_run("npm install")
                        if install_result.exit_code != 0:
                            print("Failed to install dependencies:")
                            print(install_result.output.decode())
                            return

                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        'node', f'/app/{js_file_name}'
                    ])

                finally:
                    container.stop()
                    container.remove()

            except docker.errors.ContainerError as e:
                print(f"Container error: {e}")
            except docker.errors.ImageNotFound:
                print(f"Image {self.image_name} not found")

def main():
    runner = DockerJavaScriptRunner()
    
    if not runner.build_docker_image():
        return

    js_file_path = input("Enter the path to your JavaScript file: ")
    
    runner.run_javascript(js_file_path)

if __name__ == "__main__":
    main()

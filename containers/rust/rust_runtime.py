import docker
import os
import tempfile
import subprocess
import shutil

class DockerRustRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "rust-runner"
        self.container_name = "rust-container"
        
    def build_docker_image(self):
        dockerfile_content = '''
FROM rust:1.70
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

    def run_rust_program(self, rust_file_path):
        if not os.path.exists(rust_file_path):
            print(f"Error: File {rust_file_path} does not exist")
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, 'rust_project')
            os.makedirs(project_dir)
            
            src_dir = os.path.join(project_dir, 'src')
            os.makedirs(src_dir)
            shutil.copy2(rust_file_path, os.path.join(src_dir, 'main.rs'))
            
            cargo_toml_content = '''
[package]
name = "rust_project"
version = "0.1.0"
edition = "2021"

[dependencies]
'''
            with open(os.path.join(project_dir, 'Cargo.toml'), 'w') as f:
                f.write(cargo_toml_content)
            
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
                    volumes={project_dir: {'bind': '/app', 'mode': 'rw'}},
                    detach=True,
                )
                
                try:
                    print("Building Rust program...")
                    build_result = container.exec_run(
                        "cargo build --release",
                        workdir="/app"
                    )
                    if build_result.exit_code != 0:
                        print("Build failed:")
                        print(build_result.output.decode())
                        return
                    print("Program built successfully")
                    
                    print("\nProgram output:")
                    subprocess.run([
                        'docker', 'exec', '-it', self.container_name,
                        '/app/target/release/rust_project'
                    ])
                finally:
                    container.stop()
                    container.remove()
            except docker.errors.ContainerError as e:
                print(f"Container error: {e}")
            except docker.errors.ImageNotFound:
                print(f"Image {self.image_name} not found")

def main():
    runner = DockerRustRunner()
    
    if not runner.build_docker_image():
        return
    
    rust_file_path = input("Enter the path to your Rust file: ")
    
    runner.run_rust_program(rust_file_path)

if __name__ == "__main__":
    main()

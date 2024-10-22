import docker
import os
import tempfile
import subprocess

class DockerCppRunner:
    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "cpp-runner"
        self.container_name = "cpp-container"
        
    def build_docker_image(self, packages=None):
        # Enhanced Dockerfile content with more complete dependencies
        dockerfile_content = '''
FROM gcc:latest
WORKDIR /app

# Update package list and install packages
RUN apt-get update && \\
    DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    pkg-config \\
    cmake \\
'''
        # Add core dependencies
        core_dependencies = [
            'libopencv-dev',
            'libopencv-contrib-dev',  # Add contrib modules
            'libtbb-dev',             # Threading Building Blocks
            'libatlas-base-dev',      # Linear algebra library
            'libgtk-3-dev',           # GTK for GUI
            'libavcodec-dev',         # Video codecs
            'libavformat-dev',        # Video formats
            'libswscale-dev',         # Video scaling
            'libjpeg-dev',            # JPEG support
            'libpng-dev',             # PNG support
            'libtiff-dev',            # TIFF support
            'libopenexr-dev',         # OpenEXR support
            'libwebp-dev',            # WebP support
        ]
        
        # Combine core dependencies with user-specified packages
        all_packages = core_dependencies + (packages if packages else [])
        
        dockerfile_content += '    ' + ' \\\n    '.join(all_packages) + ' && \\\n'
        dockerfile_content += '    apt-get clean && \\\n'
        dockerfile_content += '    rm -rf /var/lib/apt/lists/*\n'

        with tempfile.TemporaryDirectory() as tmpdir:
            dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            print("Building Docker image (this may take a while)...")
            try:
                self.client.images.remove(self.image_name, force=True)
            except docker.errors.ImageNotFound:
                pass
            
            try:
                build_output = self.client.images.build(
                    path=tmpdir, 
                    tag=self.image_name, 
                    nocache=True
                )
                for line in build_output[1]:
                    if 'stream' in line:
                        print(line['stream'].strip())
                print("Docker image built successfully")
            except docker.errors.BuildError as e:
                print(f"Failed to build Docker image: {e}")
                return False
        return True

    def get_opencv_libs(self, container):
        result = container.exec_run("pkg-config --libs opencv4")
        if result.exit_code == 0:
            return result.output.decode().strip()
        return ""

    def compile_and_run(self, cpp_file_path):
        if not os.path.exists(cpp_file_path):
            print(f"Error: File {cpp_file_path} does not exist")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            cpp_file_name = os.path.basename(cpp_file_path)
            temp_cpp_file = os.path.join(tmpdir, cpp_file_name)
            subprocess.run(['cp', cpp_file_path, temp_cpp_file])

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
                    # Get OpenCV compilation flags
                    opencv_libs = self.get_opencv_libs(container)
                    
                    compile_command = f"g++ -o /app/program /app/{cpp_file_name} -std=c++17 `pkg-config --cflags opencv4` {opencv_libs}"
                    
                    print("Compiling with command:")
                    print(compile_command)
                    exec_result = container.exec_run(compile_command)
                    
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

def get_package_suggestions():
    return {
        'OpenCV': 'libopencv-dev',
        'Boost': 'libboost-all-dev',
        'OpenSSL': 'libssl-dev',
        'cURL': 'libcurl4-openssl-dev',
        'GTK': 'libgtk-3-dev',
        'SQLite': 'libsqlite3-dev',
        'ZLib': 'zlib1g-dev',
        'JSON': 'nlohmann-json3-dev',
        'XML': 'libxml2-dev',
        'OpenGL': 'libglfw3-dev mesa-common-dev',
    }

def main():
    runner = DockerCppRunner()
    
    suggestions = get_package_suggestions()
    print("Common package suggestions:")
    for lib, pkg in suggestions.items():
        print(f"- {lib}: {pkg}")
    print("\nYou can specify these or any other packages you need.")
    
    packages_input = input("\nEnter required packages (space-separated) or press Enter for none: ").strip()
    packages = packages_input.split() if packages_input else []
    
    if not runner.build_docker_image(packages):
        return
    
    cpp_file_path = input("Enter the path to your C++ file: ")
    
    runner.compile_and_run(cpp_file_path)

if __name__ == "__main__":
    main()

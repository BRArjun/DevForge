import asyncio
import websockets
import json
import logging
from containers.py.py_runtime import DockerPythonRunner
from containers.cpp.cpp_runtime import DockerCppRunner
from containers.c.c_runtime import DockerCRunner
from containers.go.go_runtime import DockerGoRunner
from containers.java.java_runtime import DockerJavaRunner
from containers.js.js_runtime import DockerJavaScriptRunner
from containers.rust.rust_runtime import DockerRustRunner

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

docker_runners = {
    'python': DockerPythonRunner(),
    'cpp': DockerCppRunner(),
    'c': DockerCRunner(),
    'go': DockerGoRunner(),
    'java': DockerJavaRunner(),
    'javascript': DockerJavaScriptRunner(),
    'rust': DockerRustRunner()
}
active_containers = {}

async def handle_websocket(websocket, path):
    docker_runner = None
    try:
        async for message in websocket:
            data = json.loads(message)
            command_type = data.get('type')
            
            if command_type == 'create_file':
                file_path = data.get('file_path')
                content = data.get('content')
                language = data.get('language')
                docker_runner = docker_runners.get(language)
                if docker_runner:
                    docker_runner.create_file(file_path, content)
                    await websocket.send(json.dumps({
                        'type': 'file_created',
                        'file_path': file_path
                    }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'content': f'Unsupported language: {language}'
                    }))
            
            elif command_type == 'execute_command':
                command = data.get('command')
                language = data.get('language')
                docker_runner = docker_runners.get(language)
                if docker_runner:
                    try:
                        for output in docker_runner.execute_command(command):
                            await websocket.send(json.dumps({
                                'type': 'output',
                                'content': output
                            }))
                    except Exception as e:
                        logger.error(f"Error during command execution: {e}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'content': f'Error during command execution: {str(e)}'
                        }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'content': f'Unsupported language: {language}'
                    }))

            elif command_type == 'input':
                # ... (handle input if needed)
                pass

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Unexpected error in handle_websocket: {e}")



async def send_container_output(websocket, container_id, docker_runner):
    try:
        for output in docker_runner.get_container_output(container_id):
            await websocket.send(json.dumps({
                'type': 'output',
                'content': output
            }))
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed while sending output")
    except Exception as e:
        logger.error(f"Unexpected error in send_container_output: {e}")
        await websocket.send(json.dumps({
            'type': 'error',
            'content': str(e)
        }))

async def main():
    server = await websockets.serve(handle_websocket, "localhost", 8000)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

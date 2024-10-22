import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Terminal, Code, Package } from 'lucide-react';
import { Card } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import FileSystem from './FileSystem';
// import {comma} from 'postcss/lib/list';

const languageTemplates = {
  python: '# Write your Python code here\nprint("Hello, World!")\nname = input("Enter your name: ")\nprint(f"Hello, {name}!")',
  cpp: '#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}',
  c: '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
  go: 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
  java: 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
  javascript: 'console.log("Hello, World!");',
  rust: 'fn main() {\n    println!("Hello, World!");\n}'
};

const CodeEditor = () => {
	const [selectedFile, setSelectedFile] = useState(null);
    const [language, setLanguage] = useState('python');
    const [code, setCode] = useState('');
    const [fileContents, setFileContents] = useState({});
    const [output, setOutput] = useState('');
    const [isRunning, setIsRunning] = useState(false);
    const [ws, setWs] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [command, setCommand] = useState('');
    const [userInput, setUserInput] = useState('');
    const [packageName, setPackageName] = useState('');
    const [interactiveInput, setInteractiveInput] = useState('');
    const outputRef = useRef(null);
    const pingIntervalRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const [fileStructure, setFileStructure] = useState([]);	

    const connectWebSocket = useCallback(() => {
		const websocket = new WebSocket('ws://localhost:8000/ws/' + Math.random());
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
      setWs(websocket);
      setConnectionStatus('connected');
      
      pingIntervalRef.current = setInterval(() => {
        if (websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({ type: 'ping' }));
        }
      }, 20000);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'output') {
        setOutput(prev => prev + data.content);
        setIsRunning(false);
      } else if (data.type === 'pong') {
        console.log('Received pong from server');
      } else if (data.type === 'run_code') {
        setOutput(prev => prev + data.content);
        setIsRunning(false);
      } else if (data.type === 'execute_command') {
        setOutput(prev => prev + data.content);
        setIsRunning(false);
      } else if (data.type === 'install_package') {
        setOutput(prev => prev + data.content);
        setIsRunning(false);
      } else if (data.type === 'input') {
        setOutput(prev => prev + data.content);
        setIsRunning(false);
      } else if (data.type === 'interactive_output') { // P9ef5
        setOutput(prev => prev + data.content);
      }
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected. Attempting to reconnect...');
      setWs(null);
      setConnectionStatus('disconnected');
      clearInterval(pingIntervalRef.current);
      
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    return websocket;
  }, []);

  useEffect(() => {
    const websocket = connectWebSocket();

    return () => {
      clearInterval(pingIntervalRef.current);
      clearTimeout(reconnectTimeoutRef.current);
      if (websocket) {
        websocket.close();
      }
    };
  }, [connectWebSocket]);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

    const installPackage = () => {
    if (!ws) return;
    setIsRunning(true);
    setOutput('');
    
    ws.send(JSON.stringify({
      type: 'install_package',
      package_name: packageName
    }));
  };

    const sendInput = () => {
    if (!ws) return;
    
    ws.send(JSON.stringify({
      type: 'input',
      input: userInput
    }));
    
    setUserInput('');
  };

    const handleInteractiveInput = (e) => { // Pfdf9
    if (e.key === 'Enter') {
      if (!ws) return;
      ws.send(JSON.stringify({
        type: 'interactive_input',
        input: interactiveInput
      }));
      setInteractiveInput('');
    }
  };

    const handleLanguageChange = (value) => {
    if (selectedFile) {
      setFileContents((prev) => ({
        ...prev,
        [selectedFile.name]: code,
      }));
    }
    setLanguage(value);
    if (!selectedFile) {
      setCode(languageTemplates[value]);
    }
  };

    const selectFile = (file) => {
    if (selectedFile) {
      setFileContents((prev) => ({
        ...prev,
        [selectedFile.name]: code,
      }));
    }
    setSelectedFile(file);
    setCode(fileContents[file.name] || '');
    const fileExtension = file.name.split('.').pop();
    const languageMap = {
      py: 'python',
      cpp: 'cpp',
      c: 'c',
      go: 'go',
      java: 'java',
      js: 'javascript',
      rs: 'rust'
    };
    setLanguage(languageMap[fileExtension] || 'python');
  };

    const saveFileContent = () => {
      if (selectedFile) {
        setFileContents((prev) => ({
          ...prev,
          [selectedFile.name]: code,
        }));
      }
	};

	const executeCommand = () => {
		if (!ws || !selectedFile) return;
		setIsRunning(true);
		setOutput('');

		// First, create/update the file
    ws.send(JSON.stringify({
    type: 'create_file',
    file_path: selectedFile.name,
    content: code,
    language: language
    }));

	

    setTimeout(() => {
    const fileStructureToSend = fileStructure.map(file => ({
      path: file.name,
      type: file.type,
      content: fileContents[file.name] || ''
    }));


    const fullCommand = command.includes(selectedFile.name) ? command : `${command} ${selectedFile.name}`;

    ws.send(JSON.stringify({
      type: 'execute_command',
      command: fullCommand,
      file_structure: fileStructureToSend,
      language: language
    }));
  }, 1000);
};

  return (
    <div className="flex gap-4 w-full max-w-6xl mx-auto p-4">
      <FileSystem 
		onSelectFile={selectFile}
		onFileStructureChange={(newStructure) => setFileStructure(newStructure)}
	  />
      <div className="flex flex-col gap-4 w-2/3">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Code className="w-5 h-5" />
              <h2 className="text-lg font-semibold">Code Editor</h2>
            </div>
            <Select value={language} onValueChange={handleLanguageChange}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select Language" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="python">Python</SelectItem>
                <SelectItem value="cpp">C++</SelectItem>
                <SelectItem value="c">C</SelectItem>
                <SelectItem value="go">Go</SelectItem>
                <SelectItem value="java">Java</SelectItem>
                <SelectItem value="javascript">JavaScript</SelectItem>
                <SelectItem value="rust">Rust</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Textarea
            value={code}
            onChange={(e) => {
              setCode(e.target.value);
              if (selectedFile) {
                setFileContents((prev) => ({
                  ...prev,
                  [selectedFile.name]: e.target.value,
                }));
              }
            }}
            className="font-mono min-h-[300px] mb-4"
            placeholder={selectedFile ? `Edit ${selectedFile.name}...` : `Write your ${language} code here...`}
          />
          <button onClick={saveFileContent} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Save
          </button>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              <h2 className="text-lg font-semibold">Output</h2>
            </div>
            <div className={`px-2 py-1 rounded-full text-sm ${
              connectionStatus === 'connected' ? 'bg-green-500 text-white' :
              connectionStatus === 'disconnected' ? 'bg-yellow-500 text-black' :
              'bg-red-500 text-white'
            }`}>
              {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
            </div>
          </div>
          
          <pre
            ref={outputRef}
            className="bg-black text-green-400 p-4 rounded-lg min-h-[200px] max-h-[400px] overflow-auto font-mono whitespace-pre-wrap"
          >
            {output}
          </pre>

          <div className="flex gap-2 mt-4">
            <Input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter input for the program..."
              className="flex-grow"
            />
            <button onClick={sendInput} disabled={!isRunning} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Send Input
            </button>
          </div>
        </Card>
      

        {/* Terminal Card */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              <h2 className="text-lg font-semibold">Terminal</h2>
            </div>
          </div>
          
          <div className="flex gap-2 mb-4">
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Enter terminal command"
              className="flex-grow"
            />
            <button onClick={executeCommand} disabled={!selectedFile || connectionStatus !== 'connected'} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Execute
            </button>
          </div>

          <div className="flex gap-2 mt-4">
            <Input
              value={interactiveInput}
              onChange={(e) => setInteractiveInput(e.target.value)}
              onKeyPress={handleInteractiveInput}
              placeholder="Enter interactive input..."
              className="flex-grow"
            />
            <button onClick={() => handleInteractiveInput({ key: 'Enter' })} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Send Interactive Input
            </button>
          </div>
        </Card>

        {/* Package Installation Card */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5" />
              <h2 className="text-lg font-semibold">Package Installation</h2>
            </div>
          </div>
          
          <div className="flex gap-2 mb-4">
            <Input
              value={packageName}
              onChange={(e) => setPackageName(e.target.value)}
              placeholder="Enter package name"
              className="flex-grow"
            />
            <button onClick={installPackage} disabled={connectionStatus !== 'connected'} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
              Install Package
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default CodeEditor;

import React, { useState } from 'react';
import { Terminal } from 'lucide-react';
import { Card } from "./ui/card";
import { Input } from "./ui/input";

const TerminalComponent = ({ ws }) => {
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState('');
  const [interactiveInput, setInteractiveInput] = useState(''); // Pbb52

  const runCommand = () => {
    if (!ws) return;
    
    ws.send(JSON.stringify({
      type: 'run_command',
      command: command
    }));

    setOutput(prev => prev + '$ ' + command + '\n');
    setCommand('');
  };

  const handleCommand = (e) => {
    if (e.key === 'Enter') {
      runCommand();
    }
  };

  const handleInteractiveInput = (e) => { // P112a
    if (e.key === 'Enter') {
      if (!ws) return;
      ws.send(JSON.stringify({
        type: 'interactive_input',
        input: interactiveInput
      }));
      setInteractiveInput('');
    }
  };

  const handleRenameCommand = (filePath, newName) => {
    if (!ws) return;

    ws.send(JSON.stringify({
      type: 'rename_file',
      file_path: filePath,
      new_name: newName
    }));

    setOutput(prev => prev + `Renamed ${filePath} to ${newName}\n`);
  };

  const handleDeleteCommand = (filePath) => {
    if (!ws) return;

    ws.send(JSON.stringify({
      type: 'delete_file',
      file_path: filePath
    }));

    setOutput(prev => prev + `Deleted ${filePath}\n`);
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Terminal className="w-5 h-5" />
        <h2 className="text-lg font-semibold">Terminal</h2>
      </div>
      
      <pre className="bg-black text-green-400 p-4 rounded-lg min-h-[200px] max-h-[400px] overflow-auto font-mono whitespace-pre-wrap mb-4">
        {output}
      </pre>

      <Input
        type="text"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        onKeyPress={handleCommand}
        placeholder="Enter command..."
        className="w-full p-2 border rounded"
      />

      <Input
        type="text"
        value={interactiveInput}
        onChange={(e) => setInteractiveInput(e.target.value)}
        onKeyPress={handleInteractiveInput}
        placeholder="Enter interactive input..."
        className="w-full p-2 border rounded mt-4"
      />
    </Card>
  );
};

export default TerminalComponent;

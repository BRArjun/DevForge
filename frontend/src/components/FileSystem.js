import React, { useState } from 'react';
import { Folder, File, Plus, Trash, Edit } from 'lucide-react';

const FileSystem = ({ onSelectFile }) => {
  const [fileStructure, setFileStructure] = useState([
    { id: 1, name: 'Root', type: 'folder', children: [] },
  ]);
  const [newFileName, setNewFileName] = useState('');
  const [newFolderName, setNewFolderName] = useState('');
  const [renamingItem, setRenamingItem] = useState(null);
  const [renamingName, setRenamingName] = useState('');

  const addFile = (folderId) => {
    if (!newFileName.trim()) return;
    const updatedStructure = addToFileStructure(fileStructure, folderId, {
      id: Date.now(),
      name: newFileName,
      type: 'file',
      content: '',
    });
    setFileStructure(updatedStructure);
    setNewFileName('');
  };

  const addFolder = (folderId) => {
    if (!newFolderName.trim()) return;
    const updatedStructure = addToFileStructure(fileStructure, folderId, {
      id: Date.now(),
      name: newFolderName,
      type: 'folder',
      children: [],
    });
    setFileStructure(updatedStructure);
    setNewFolderName('');
  };

  const addToFileStructure = (structure, folderId, item) => {
    return structure.map((node) => {
      if (node.id === folderId && node.type === 'folder') {
        return {
          ...node,
          children: [...node.children, item],
        };
      } else if (node.children) {
        return {
          ...node,
          children: addToFileStructure(node.children, folderId, item),
        };
      }
      return node;
    });
  };

  const deleteItem = (structure, itemId) => {
    return structure.filter((node) => {
      if (node.id === itemId) {
        return false;
      }
      if (node.children) {
        node.children = deleteItem(node.children, itemId);
      }
      return true;
    });
  };

  const renameItem = (structure, itemId, newName) => {
    return structure.map((node) => {
      if (node.id === itemId) {
        return {
          ...node,
          name: newName,
        };
      }
      if (node.children) {
        return {
          ...node,
          children: renameItem(node.children, itemId, newName),
        };
      }
      return node;
    });
  };

  const renderStructure = (structure) => {
    return structure.map((node) => (
      <div key={node.id} style={{ marginLeft: '20px' }}>
        {node.type === 'folder' ? (
          <div>
            <Folder className="inline-block" /> {node.name}
            <button onClick={() => addFile(node.id)}>
              <Plus size={14} /> File
            </button>
            <button onClick={() => addFolder(node.id)}>
              <Plus size={14} /> Folder
            </button>
            <button onClick={() => setRenamingItem(node)}>
              <Edit size={14} /> Rename
            </button>
            <button onClick={() => setFileStructure(deleteItem(fileStructure, node.id))}>
              <Trash size={14} /> Delete
            </button>
            {renderStructure(node.children)}
          </div>
        ) : (
          <div onClick={() => onSelectFile(node)}>
            <File className="inline-block" /> {node.name}
            <button onClick={() => setRenamingItem(node)}>
              <Edit size={14} /> Rename
            </button>
            <button onClick={() => setFileStructure(deleteItem(fileStructure, node.id))}>
              <Trash size={14} /> Delete
            </button>
          </div>
        )}
      </div>
    ));
  };

  const handleRename = () => {
    if (!renamingName.trim()) return;
    const updatedStructure = renameItem(fileStructure, renamingItem.id, renamingName);
    setFileStructure(updatedStructure);
    setRenamingItem(null);
    setRenamingName('');
  };

  return (
    <div className="p-4">
      <h3>File System</h3>
      <input
        type="text"
        value={newFileName}
        onChange={(e) => setNewFileName(e.target.value)}
        placeholder="New File Name"
      />
      <button onClick={() => addFile(1)}>
        <Plus size={14} /> Add File to Root
      </button>
      <input
        type="text"
        value={newFolderName}
        onChange={(e) => setNewFolderName(e.target.value)}
        placeholder="New Folder Name"
      />
      <button onClick={() => addFolder(1)}>
        <Plus size={14} /> Add Folder to Root
      </button>
      <div>{renderStructure(fileStructure)}</div>
      {renamingItem && (
        <div>
          <input
            type="text"
            value={renamingName}
            onChange={(e) => setRenamingName(e.target.value)}
            placeholder="New Name"
          />
          <button onClick={handleRename}>
            <Edit size={14} /> Rename
          </button>
        </div>
      )}
    </div>
  );
};

export default FileSystem;

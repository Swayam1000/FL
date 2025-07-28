import React, { useEffect, useState } from 'react';
import { ethers } from 'ethers';
import MetadataStorage from './artifacts/contracts/MetadataStorage.sol/MetadataStorage.json';
import './App.css';

const contractAddress = '0x2780ca5e0E07b8F0dD066b4a232D0C05fc89De1A';

function App() {
  const [contract, setContract] = useState(null);
  const [metadataList, setMetadataList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [customKey, setCustomKey] = useState('');
  const [customValue, setCustomValue] = useState('');
  const [selectedMetadataId, setSelectedMetadataId] = useState('');

  useEffect(() => {
    const initializeContract = async () => {
      try {
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        const provider = new ethers.BrowserProvider(window.ethereum);
        const signer = await provider.getSigner();
        const metadataContract = new ethers.Contract(
          contractAddress,
          MetadataStorage.abi,
          signer
        );
        setContract(metadataContract);

        // Set up event listeners
        metadataContract.on('MetadataCreated', (id, title, owner, fileHash) => {
          console.log('New metadata created:', { id, title, owner, fileHash });
          loadMetadataList();
        });

        loadMetadataList();
      } catch (err) {
        console.error('Error initializing contract:', err);
        setError('Failed to initialize contract');
      }
    };

    initializeContract();
    return () => {
      if (contract) {
        contract.removeAllListeners();
      }
    };
  }, []);

  // Function to calculate file hash
  const calculateFileHash = async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const buffer = e.target.result;
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        resolve(hashHex);
      };
      reader.onerror = reject;
      reader.readAsArrayBuffer(file);
    });
  };

  const loadMetadataList = async () => {
    if (!contract) return;
    
    try {
      setLoading(true);
      const count = await contract.getMetadataCount();
      const metadataItems = [];
      
      for (let i = 0; i < count; i++) {
        const metadata = await contract.getMetadata(i);
        metadataItems.push({
          id: i,
          title: metadata[0],
          description: metadata[1],
          owner: metadata[2],
          timestamp: new Date(Number(metadata[3]) * 1000).toLocaleString(),
          tags: metadata[4],
          fileHash: metadata[5]
        });
      }
      
      setMetadataList(metadataItems);
    } catch (err) {
      console.error('Error loading metadata:', err);
      setError('Failed to load metadata list');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleCreateMetadata = async (e) => {
    e.preventDefault();
    if (!contract || !selectedFile) return;

    try {
      setLoading(true);
      setError('');
      
      // Calculate file hash
      const fileHash = await calculateFileHash(selectedFile);
      console.log('File hash:', fileHash);

      const tagArray = tags.split(',').map(tag => tag.trim());
      const tx = await contract.createMetadata(title, description, tagArray, fileHash);
      await tx.wait();
      
      // Clear form
      setTitle('');
      setDescription('');
      setTags('');
      setSelectedFile(null);
      
      await loadMetadataList();
    } catch (err) {
      console.error('Error creating metadata:', err);
      setError('Failed to create metadata');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomField = async (e) => {
    e.preventDefault();
    if (!contract || !selectedMetadataId) return;

    try {
      setLoading(true);
      setError('');
      const tx = await contract.addCustomField(selectedMetadataId, customKey, customValue);
      await tx.wait();
      
      // Clear form
      setCustomKey('');
      setCustomValue('');
      setSelectedMetadataId('');
      
      await loadMetadataList();
    } catch (err) {
      console.error('Error adding custom field:', err);
      setError('Failed to add custom field');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Metadata Storage DApp</h1>
      
      {error && <div className="error">{error}</div>}
      
      <div className="form-section">
        <h2>Create New Metadata</h2>
        <form onSubmit={handleCreateMetadata}>
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Tags (comma-separated)"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            required
          />
          <input
            type="file"
            onChange={handleFileChange}
            required
          />
          <button type="submit" disabled={loading || !selectedFile}>
            {loading ? 'Creating...' : 'Create Metadata'}
          </button>
        </form>
      </div>

      <div className="form-section">
        <h2>Add Custom Field</h2>
        <form onSubmit={handleAddCustomField}>
          <select
            value={selectedMetadataId}
            onChange={(e) => setSelectedMetadataId(e.target.value)}
            required
          >
            <option value="">Select Metadata</option>
            {metadataList.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Custom Field Key"
            value={customKey}
            onChange={(e) => setCustomKey(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Custom Field Value"
            value={customValue}
            onChange={(e) => setCustomValue(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Adding...' : 'Add Custom Field'}
          </button>
        </form>
      </div>

      <div className="metadata-list">
        <h2>Metadata List</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="metadata-grid">
            {metadataList.map((item) => (
              <div key={item.id} className="metadata-card">
                <h3>{item.title}</h3>
                <p>{item.description}</p>
                <p><strong>Tags:</strong> {item.tags.join(', ')}</p>
                <p><strong>File Hash:</strong> {item.fileHash}</p>
                <p><strong>Owner:</strong> {item.owner}</p>
                <p><strong>Created:</strong> {item.timestamp}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

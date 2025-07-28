// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MetadataStorage {
    // Structure to hold metadata
    struct Metadata {
        string title;
        string description;
        address owner;
        uint256 timestamp;
        string[] tags;
        string fileHash;  // Added field for file hash
        mapping(string => string) customFields;
    }

    // Mapping from metadata ID to Metadata struct
    mapping(uint256 => Metadata) private metadataStore;
    uint256 private metadataCount;

    // Events
    event MetadataCreated(uint256 indexed id, string title, address owner, string fileHash);
    event MetadataUpdated(uint256 indexed id, string title, address owner);
    event CustomFieldAdded(uint256 indexed id, string key, string value);
    event FileHashUpdated(uint256 indexed id, string fileHash);

    // Create new metadata with file hash
    function createMetadata(
        string memory _title,
        string memory _description,
        string[] memory _tags,
        string memory _fileHash
    ) public returns (uint256) {
        uint256 metadataId = metadataCount++;
        
        Metadata storage newMetadata = metadataStore[metadataId];
        newMetadata.title = _title;
        newMetadata.description = _description;
        newMetadata.owner = msg.sender;
        newMetadata.timestamp = block.timestamp;
        newMetadata.tags = _tags;
        newMetadata.fileHash = _fileHash;

        emit MetadataCreated(metadataId, _title, msg.sender, _fileHash);
        return metadataId;
    }

    // Update file hash for existing metadata
    function updateFileHash(uint256 _id, string memory _newFileHash) public {
        require(_id < metadataCount, "Metadata does not exist");
        require(msg.sender == metadataStore[_id].owner, "Not the owner");
        
        metadataStore[_id].fileHash = _newFileHash;
        emit FileHashUpdated(_id, _newFileHash);
    }

    // Add custom field to existing metadata
    function addCustomField(
        uint256 _id,
        string memory _key,
        string memory _value
    ) public {
        require(_id < metadataCount, "Metadata does not exist");
        require(msg.sender == metadataStore[_id].owner, "Not the owner");
        
        metadataStore[_id].customFields[_key] = _value;
        emit CustomFieldAdded(_id, _key, _value);
    }

    // Get metadata details
    function getMetadata(uint256 _id) public view returns (
        string memory title,
        string memory description,
        address owner,
        uint256 timestamp,
        string[] memory tags,
        string memory fileHash
    ) {
        require(_id < metadataCount, "Metadata does not exist");
        Metadata storage metadata = metadataStore[_id];
        
        return (
            metadata.title,
            metadata.description,
            metadata.owner,
            metadata.timestamp,
            metadata.tags,
            metadata.fileHash
        );
    }

    // Get custom field value
    function getCustomField(
        uint256 _id,
        string memory _key
    ) public view returns (string memory) {
        require(_id < metadataCount, "Metadata does not exist");
        return metadataStore[_id].customFields[_key];
    }

    // Get total number of metadata entries
    function getMetadataCount() public view returns (uint256) {
        return metadataCount;
    }
}

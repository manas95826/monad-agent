// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CertificateAuthenticator {
    struct Certificate {
        uint256 id;
        string name;
        string certificateHash;
        uint256 timestamp;
        address issuer;
        bool isValid;
    }
    
    uint256 public nextCertificateId;
    mapping(uint256 => Certificate) public certificates;
    mapping(string => bool) public certificateHashExists;
    mapping(address => uint256[]) private userCertificates;
    
    event CertificateIssued(
        uint256 certificateId,
        address indexed issuer,
        string name,
        string certificateHash,
        uint256 timestamp
    );
    
    event CertificateRevoked(uint256 certificateId);
    
    constructor() {
        nextCertificateId = 1;
    }
    
    function issueCertificate(
        string memory _name,
        string memory _certificateHash
    ) external {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_certificateHash).length > 0, "Certificate hash cannot be empty");
        require(!certificateHashExists[_certificateHash], "Certificate hash already exists");
        
        uint256 certificateId = nextCertificateId++;
        
        certificates[certificateId] = Certificate({
            id: certificateId,
            name: _name,
            certificateHash: _certificateHash,
            timestamp: block.timestamp,
            issuer: msg.sender,
            isValid: true
        });
        
        certificateHashExists[_certificateHash] = true;
        userCertificates[msg.sender].push(certificateId);
        
        emit CertificateIssued(certificateId, msg.sender, _name, _certificateHash, block.timestamp);
    }
    
    function revokeCertificate(uint256 _certificateId) external {
        Certificate storage cert = certificates[_certificateId];
        require(cert.id != 0, "Certificate does not exist");
        require(msg.sender == cert.issuer, "Only issuer can revoke certificate");
        require(cert.isValid, "Certificate already revoked");
        
        cert.isValid = false;
        emit CertificateRevoked(_certificateId);
    }
    
    function verifyCertificate(string memory _certificateHash) external view returns (bool) {
        return certificateHashExists[_certificateHash];
    }
    
    function getCertificate(uint256 _certificateId) external view returns (Certificate memory) {
        require(certificates[_certificateId].id != 0, "Certificate does not exist");
        return certificates[_certificateId];
    }
    
    function getMyCertificates() external view returns (Certificate[] memory) {
        uint256[] storage certIds = userCertificates[msg.sender];
        Certificate[] memory result = new Certificate[](certIds.length);
        
        for (uint256 i = 0; i < certIds.length; i++) {
            result[i] = certificates[certIds[i]];
        }
        
        return result;
    }
} 
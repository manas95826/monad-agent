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

    uint256 private nextCertificateId = 1;
    mapping(uint256 => Certificate) public certificates;
    mapping(string => uint256) public hashToCertificateId;
    mapping(address => uint256[]) private userCertificates;

    event CertificateIssued(
        uint256 indexed certificateId,
        address indexed issuer,
        string name,
        string certificateHash,
        uint256 timestamp
    );

    event CertificateRevoked(uint256 indexed certificateId);

    function issueCertificate(string memory _name, string memory _certificateHash) public {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_certificateHash).length > 0, "Certificate hash cannot be empty");
        require(hashToCertificateId[_certificateHash] == 0, "Certificate hash already exists");

        uint256 certificateId = nextCertificateId++;
        
        Certificate memory newCertificate = Certificate({
            id: certificateId,
            name: _name,
            certificateHash: _certificateHash,
            timestamp: block.timestamp,
            issuer: msg.sender,
            isValid: true
        });

        certificates[certificateId] = newCertificate;
        hashToCertificateId[_certificateHash] = certificateId;
        userCertificates[msg.sender].push(certificateId);

        emit CertificateIssued(
            certificateId,
            msg.sender,
            _name,
            _certificateHash,
            block.timestamp
        );
    }

    function revokeCertificate(uint256 _certificateId) public {
        require(_certificateId > 0 && _certificateId < nextCertificateId, "Invalid certificate ID");
        Certificate storage cert = certificates[_certificateId];
        require(cert.issuer == msg.sender, "Only issuer can revoke");
        require(cert.isValid, "Certificate already revoked");
        
        cert.isValid = false;
        emit CertificateRevoked(_certificateId);
    }

    function verifyCertificate(string memory _certificateHash) public view returns (bool) {
        uint256 certificateId = hashToCertificateId[_certificateHash];
        if (certificateId == 0) return false;
        return certificates[certificateId].isValid;
    }

    function getCertificate(uint256 _certificateId) public view returns (Certificate memory) {
        require(_certificateId > 0 && _certificateId < nextCertificateId, "Invalid certificate ID");
        return certificates[_certificateId];
    }

    function getMyCertificates() public view returns (Certificate[] memory) {
        uint256[] memory certIds = userCertificates[msg.sender];
        Certificate[] memory result = new Certificate[](certIds.length);
        
        for (uint256 i = 0; i < certIds.length; i++) {
            result[i] = certificates[certIds[i]];
        }
        
        return result;
    }
}
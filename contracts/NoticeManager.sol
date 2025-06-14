// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title NoticeManager
 * @dev A smart contract for managing notices and guidelines through Monad blockchain
 */
contract NoticeManager {
    struct Notice {
        uint256 id;
        string category;
        string description;
        uint8 priority;
        string content;
        address sender;
        uint256 timestamp;
    }

    // Mapping from notice ID to Notice
    mapping(uint256 => Notice) public notices;
    
    // Mapping from category to array of notice IDs
    mapping(string => uint256[]) public noticesByCategory;
    
    // Counter for notice IDs
    uint256 private _noticeIdCounter;
    
    // Event emitted when a new notice is created
    event NoticeCreated(
        uint256 indexed noticeId,
        address indexed sender,
        string category,
        string description,
        uint8 priority,
        string content,
        uint256 timestamp
    );

    constructor() {
        _noticeIdCounter = 1;
    }

    /**
     * @dev Creates a new notice
     * @param _category The category of the notice
     * @param _description Brief description of the notice
     * @param _priority Priority level (0-3)
     * @param _content The full content of the notice
     */
    function createNotice(
        string memory _category,
        string memory _description,
        uint8 _priority,
        string memory _content
    ) public {
        require(_priority <= 3, "Priority must be between 0 and 3");
        require(bytes(_category).length > 0, "Category cannot be empty");
        require(bytes(_description).length > 0, "Description cannot be empty");
        require(bytes(_content).length > 0, "Content cannot be empty");

        uint256 noticeId = _noticeIdCounter++;
        
        Notice memory newNotice = Notice({
            id: noticeId,
            category: _category,
            description: _description,
            priority: _priority,
            content: _content,
            sender: msg.sender,
            timestamp: block.timestamp
        });

        notices[noticeId] = newNotice;
        noticesByCategory[_category].push(noticeId);

        emit NoticeCreated(
            noticeId,
            msg.sender,
            _category,
            _description,
            _priority,
            _content,
            block.timestamp
        );
    }

    /**
     * @dev Gets a specific notice by ID
     * @param _noticeId The ID of the notice to retrieve
     * @return The notice details
     */
    function getNotice(uint256 _noticeId) public view returns (Notice memory) {
        require(_noticeId > 0 && _noticeId < _noticeIdCounter, "Invalid notice ID");
        return notices[_noticeId];
    }

    /**
     * @dev Gets all notices for a specific category
     * @param _category The category to filter notices by
     * @return Array of notices in the category
     */
    function getNoticesByCategory(string memory _category) public view returns (Notice[] memory) {
        uint256[] memory noticeIds = noticesByCategory[_category];
        Notice[] memory categoryNotices = new Notice[](noticeIds.length);
        
        for (uint256 i = 0; i < noticeIds.length; i++) {
            categoryNotices[i] = notices[noticeIds[i]];
        }
        
        return categoryNotices;
    }

    /**
     * @dev Gets the total number of notices
     * @return The total number of notices created
     */
    function getTotalNotices() public view returns (uint256) {
        return _noticeIdCounter - 1;
    }
} 
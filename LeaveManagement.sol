// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title LeaveManagement
 * @dev Smart contract for managing employee leaves, attendance, and holidays
 */
contract LeaveManagement {
    // Structs
    struct Leave {
        uint256 id;
        uint256 startDate;
        uint256 endDate;
        string leaveType;
        string reason;
        address employee;
        uint8 status; // 0: Pending, 1: Approved, 2: Rejected
    }

    struct Holiday {
        uint256 date;
        string description;
    }

    struct Attendance {
        uint256 date;
        bool present;
    }

    // State variables
    mapping(uint256 => Leave) public leaves;
    mapping(address => uint256[]) public employeeLeaves;
    mapping(uint256 => Holiday) public holidays;
    mapping(address => mapping(uint256 => bool)) public attendance;
    mapping(address => uint256[]) public employeeAttendance;

    uint256 public leaveCounter;
    address public owner;

    // Events
    event LeaveRequested(
        uint256 indexed leaveId,
        address indexed employee,
        uint256 startDate,
        uint256 endDate,
        string leaveType,
        string reason
    );

    event LeaveStatusUpdated(
        uint256 indexed leaveId,
        address indexed approver,
        uint8 status
    );

    event HolidayAdded(
        uint256 date,
        string description
    );

    event AttendanceMarked(
        address indexed employee,
        uint256 date,
        bool present
    );

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier validLeaveType(string memory _leaveType) {
        require(
            keccak256(bytes(_leaveType)) == keccak256(bytes("Annual")) ||
            keccak256(bytes(_leaveType)) == keccak256(bytes("Sick")) ||
            keccak256(bytes(_leaveType)) == keccak256(bytes("Personal")) ||
            keccak256(bytes(_leaveType)) == keccak256(bytes("Maternity/Paternity")) ||
            keccak256(bytes(_leaveType)) == keccak256(bytes("Unpaid")),
            "Invalid leave type"
        );
        _;
    }

    modifier validStatus(uint8 _status) {
        require(_status <= 2, "Invalid status");
        _;
    }

    // Constructor
    constructor() {
        owner = msg.sender;
        leaveCounter = 1;
    }

    /**
     * @dev Request a new leave
     * @param _startDate Start date of leave (Unix timestamp)
     * @param _endDate End date of leave (Unix timestamp)
     * @param _leaveType Type of leave
     * @param _reason Reason for leave
     */
    function requestLeave(
        uint256 _startDate,
        uint256 _endDate,
        string memory _leaveType,
        string memory _reason
    ) public validLeaveType(_leaveType) {
        require(_startDate < _endDate, "Start date must be before end date");
        require(_startDate > block.timestamp, "Cannot request leave for past dates");

        Leave memory newLeave = Leave({
            id: leaveCounter,
            startDate: _startDate,
            endDate: _endDate,
            leaveType: _leaveType,
            reason: _reason,
            employee: msg.sender,
            status: 0 // Pending
        });

        leaves[leaveCounter] = newLeave;
        employeeLeaves[msg.sender].push(leaveCounter);

        emit LeaveRequested(
            leaveCounter,
            msg.sender,
            _startDate,
            _endDate,
            _leaveType,
            _reason
        );

        leaveCounter++;
    }

    /**
     * @dev Update leave status
     * @param _leaveId ID of the leave request
     * @param _status New status (0: Pending, 1: Approved, 2: Rejected)
     */
    function updateLeaveStatus(
        uint256 _leaveId,
        uint8 _status
    ) public onlyOwner validStatus(_status) {
        require(_leaveId < leaveCounter, "Invalid leave ID");
        require(leaves[_leaveId].employee != address(0), "Leave does not exist");

        leaves[_leaveId].status = _status;

        emit LeaveStatusUpdated(_leaveId, msg.sender, _status);
    }

    /**
     * @dev Get all leaves for the calling employee
     * @return Array of leave requests
     */
    function getMyLeaves() public view returns (Leave[] memory) {
        uint256[] memory leaveIds = employeeLeaves[msg.sender];
        Leave[] memory myLeaves = new Leave[](leaveIds.length);

        for (uint256 i = 0; i < leaveIds.length; i++) {
            myLeaves[i] = leaves[leaveIds[i]];
        }

        return myLeaves;
    }

    /**
     * @dev Get all pending leaves
     * @return Array of pending leave requests
     */
    function getPendingLeaves() public view returns (Leave[] memory) {
        uint256 pendingCount = 0;
        
        // Count pending leaves
        for (uint256 i = 1; i < leaveCounter; i++) {
            if (leaves[i].status == 0) {
                pendingCount++;
            }
        }

        // Create array of pending leaves
        Leave[] memory pendingLeaves = new Leave[](pendingCount);
        uint256 currentIndex = 0;

        for (uint256 i = 1; i < leaveCounter; i++) {
            if (leaves[i].status == 0) {
                pendingLeaves[currentIndex] = leaves[i];
                currentIndex++;
            }
        }

        return pendingLeaves;
    }

    /**
     * @dev Add a holiday to the calendar
     * @param _date Date of the holiday (Unix timestamp)
     * @param _description Description of the holiday
     */
    function addHoliday(
        uint256 _date,
        string memory _description
    ) public onlyOwner {
        require(_date > block.timestamp, "Cannot add holiday for past dates");
        require(holidays[_date].date == 0, "Holiday already exists for this date");

        holidays[_date] = Holiday({
            date: _date,
            description: _description
        });

        emit HolidayAdded(_date, _description);
    }

    /**
     * @dev Get all holidays
     * @return Array of holidays
     */
    function getHolidays() public view returns (Holiday[] memory) {
        uint256 holidayCount = 0;
        
        // Count holidays
        for (uint256 i = 1; i < type(uint256).max; i++) {
            if (holidays[i].date != 0) {
                holidayCount++;
            } else {
                break;
            }
        }

        // Create array of holidays
        Holiday[] memory allHolidays = new Holiday[](holidayCount);
        uint256 currentIndex = 0;

        for (uint256 i = 1; i < type(uint256).max; i++) {
            if (holidays[i].date != 0) {
                allHolidays[currentIndex] = holidays[i];
                currentIndex++;
            } else {
                break;
            }
        }

        return allHolidays;
    }

    /**
     * @dev Mark attendance for a specific date
     * @param _date Date to mark attendance (Unix timestamp)
     */
    function markAttendance(uint256 _date) public {
        require(_date <= block.timestamp, "Cannot mark attendance for future dates");
        require(!attendance[msg.sender][_date], "Attendance already marked for this date");

        attendance[msg.sender][_date] = true;
        employeeAttendance[msg.sender].push(_date);

        emit AttendanceMarked(msg.sender, _date, true);
    }

    /**
     * @dev Get attendance records for a date range
     * @param _startDate Start date (Unix timestamp)
     * @param _endDate End date (Unix timestamp)
     * @return Array of attendance records
     */
    function getAttendance(
        uint256 _startDate,
        uint256 _endDate
    ) public view returns (Attendance[] memory) {
        require(_startDate <= _endDate, "Invalid date range");

        uint256[] memory dates = employeeAttendance[msg.sender];
        uint256 recordCount = 0;

        // Count records in date range
        for (uint256 i = 0; i < dates.length; i++) {
            if (dates[i] >= _startDate && dates[i] <= _endDate) {
                recordCount++;
            }
        }

        // Create array of attendance records
        Attendance[] memory records = new Attendance[](recordCount);
        uint256 currentIndex = 0;

        for (uint256 i = 0; i < dates.length; i++) {
            if (dates[i] >= _startDate && dates[i] <= _endDate) {
                records[currentIndex] = Attendance({
                    date: dates[i],
                    present: attendance[msg.sender][dates[i]]
                });
                currentIndex++;
            }
        }

        return records;
    }
} 
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EmployeePayment {
    struct Payment {
        uint256 id;
        string employeeName;
        address employeeAddress;
        string description;
        uint256 amount;
        uint256 timestamp;
        bool isPaid;
    }

    mapping(uint256 => Payment) public payments;
    uint256 public paymentCount;
    address public owner;

    event PaymentCreated(
        uint256 indexed paymentId,
        string employeeName,
        address indexed employeeAddress,
        string description,
        uint256 amount,
        uint256 timestamp
    );

    event PaymentProcessed(
        uint256 indexed paymentId,
        address indexed employeeAddress,
        uint256 amount,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function createPayment(
        string memory _employeeName,
        address _employeeAddress,
        string memory _description,
        uint256 _amount
    ) public onlyOwner {
        require(_employeeAddress != address(0), "Invalid employee address");
        require(_amount > 0, "Amount must be greater than 0");

        paymentCount++;
        payments[paymentCount] = Payment({
            id: paymentCount,
            employeeName: _employeeName,
            employeeAddress: _employeeAddress,
            description: _description,
            amount: _amount,
            timestamp: block.timestamp,
            isPaid: false
        });

        emit PaymentCreated(
            paymentCount,
            _employeeName,
            _employeeAddress,
            _description,
            _amount,
            block.timestamp
        );
    }

    function processPayment(uint256 _paymentId) public payable onlyOwner {
        Payment storage payment = payments[_paymentId];
        require(!payment.isPaid, "Payment already processed");
        require(msg.value >= payment.amount, "Insufficient payment amount");

        payment.isPaid = true;
        payable(payment.employeeAddress).transfer(payment.amount);

        emit PaymentProcessed(
            _paymentId,
            payment.employeeAddress,
            payment.amount,
            block.timestamp
        );
    }

    function getPayment(uint256 _paymentId) public view returns (
        uint256 id,
        string memory employeeName,
        address employeeAddress,
        string memory description,
        uint256 amount,
        uint256 timestamp,
        bool isPaid
    ) {
        Payment memory payment = payments[_paymentId];
        return (
            payment.id,
            payment.employeeName,
            payment.employeeAddress,
            payment.description,
            payment.amount,
            payment.timestamp,
            payment.isPaid
        );
    }

    function getMyPayments() public view returns (Payment[] memory) {
        uint256 count = 0;
        for (uint256 i = 1; i <= paymentCount; i++) {
            if (payments[i].employeeAddress == msg.sender) {
                count++;
            }
        }

        Payment[] memory myPayments = new Payment[](count);
        uint256 index = 0;
        for (uint256 i = 1; i <= paymentCount; i++) {
            if (payments[i].employeeAddress == msg.sender) {
                myPayments[index] = payments[i];
                index++;
            }
        }
        return myPayments;
    }
} 
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TaskTracker {
    enum TaskStatus { Pending, InProgress, Completed, Cancelled }
    
    struct Task {
        uint256 id;
        string description;
        uint256 deadline;
        address assigner;
        address assignee;
        TaskStatus status;
    }
    
    uint256 public nextTaskId;
    mapping(uint256 => Task) public tasks;
    mapping(address => uint256[]) private userTasks;
    
    event TaskCreated(uint256 taskId, address indexed assigner, address indexed assignee, string description, uint256 deadline);
    event TaskStatusUpdated(uint256 taskId, TaskStatus newStatus);
    
    constructor() {
        nextTaskId = 1;
    }
    
    function createTask(
        string memory _description,
        uint256 _deadline,
        address _assignee
    ) external {
        require(_deadline > block.timestamp, "Deadline must be in the future");
        require(_assignee != address(0), "Invalid assignee address");
        
        uint256 taskId = nextTaskId++;
        
        tasks[taskId] = Task({
            id: taskId,
            description: _description,
            deadline: _deadline,
            assigner: msg.sender,
            assignee: _assignee,
            status: TaskStatus.Pending
        });
        
        userTasks[msg.sender].push(taskId);
        userTasks[_assignee].push(taskId);
        
        emit TaskCreated(taskId, msg.sender, _assignee, _description, _deadline);
    }
    
    function updateTaskStatus(uint256 _taskId, TaskStatus _newStatus) external {
        Task storage task = tasks[_taskId];
        require(task.id != 0, "Task does not exist");
        require(
            msg.sender == task.assigner || msg.sender == task.assignee,
            "Not authorized to update this task"
        );
        
        task.status = _newStatus;
        emit TaskStatusUpdated(_taskId, _newStatus);
    }
    
    function getMyTasks() external view returns (Task[] memory) {
        uint256[] storage taskIds = userTasks[msg.sender];
        Task[] memory result = new Task[](taskIds.length);
        
        for (uint256 i = 0; i < taskIds.length; i++) {
            result[i] = tasks[taskIds[i]];
        }
        
        return result;
    }
    
    function getTask(uint256 _taskId) external view returns (Task memory) {
        require(tasks[_taskId].id != 0, "Task does not exist");
        return tasks[_taskId];
    }
}

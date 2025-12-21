

CREATE_TASK_SCRIPT = """
local task_id = redis.call('INCR', 'task:id:counter')
local task_key = 'task:' .. task_id

-- Create task hash with all fields
redis.call('HSET', task_key,
    'id', task_id,
    'user_id', ARGV[1],
    'title', ARGV[2],
    'description', ARGV[3],
    'parent_id', ARGV[4],
    'created_at', ARGV[5],
    'completed_at', '',
    'deleted_at', '',
    'updated_at', ARGV[5]
)

-- Add to user's active tasks sorted set (scored by created_at timestamp)
local user_tasks_key = 'user:' .. ARGV[1] .. ':tasks'
redis.call('ZADD', user_tasks_key, ARGV[5], task_id)

-- If this is a subtask (parent_id != "0"), add to parent's subtasks
if ARGV[4] ~= "0" then
    local parent_subtasks_key = 'task:' .. ARGV[4] .. ':subtasks'
    redis.call('ZADD', parent_subtasks_key, ARGV[5], task_id)
end

return task_id
"""



TOGGLE_COMPLETE_SCRIPT = """
local task_key = 'task:' .. ARGV[1]
local user_id = redis.call('HGET', task_key, 'user_id')

if not user_id then
    return redis.error_reply('Task not found')
end

local current_completed_at = redis.call('HGET', task_key, 'completed_at')
local user_active_key = 'user:' .. user_id .. ':tasks'
local user_completed_key = 'user:' .. user_id .. ':tasks:completed'

if current_completed_at == '' then
    -- Mark as completed
    redis.call('HSET', task_key, 'completed_at', ARGV[2])
    redis.call('HSET', task_key, 'updated_at', ARGV[2])
    
    -- Move from active to completed sorted set
    redis.call('ZREM', user_active_key, ARGV[1])
    redis.call('ZADD', user_completed_key, ARGV[2], ARGV[1])
    
    return 'completed'
else
    -- Mark as incomplete
    redis.call('HSET', task_key, 'completed_at', '')
    redis.call('HSET', task_key, 'updated_at', ARGV[2])
    
    -- Move from completed to active sorted set
    redis.call('ZREM', user_completed_key, ARGV[1])
    local created_at = redis.call('HGET', task_key, 'created_at')
    redis.call('ZADD', user_active_key, created_at, ARGV[1])
    
    return 'incomplete'
end
"""


SOFT_DELETE_SCRIPT = """
local function soft_delete_recursive(task_id, deleted_at)
    local task_key = 'task:' .. task_id
    local user_id = redis.call('HGET', task_key, 'user_id')
    
    if not user_id then
        return 0
    end
    
    -- Check if already deleted
    local current_deleted_at = redis.call('HGET', task_key, 'deleted_at')
    if current_deleted_at ~= '' then
        return 0
    end
    
    -- Set deleted_at timestamp
    redis.call('HSET', task_key, 'deleted_at', deleted_at)
    redis.call('HSET', task_key, 'updated_at', deleted_at)
    
    -- Remove from user's active and completed sorted sets
    local user_active_key = 'user:' .. user_id .. ':tasks'
    local user_completed_key = 'user:' .. user_id .. ':tasks:completed'
    redis.call('ZREM', user_active_key, task_id)
    redis.call('ZREM', user_completed_key, task_id)
    
    local deleted_count = 1
    
    -- Get all subtasks and recursively delete
    local subtasks_key = 'task:' .. task_id .. ':subtasks'
    local subtasks = redis.call('ZRANGE', subtasks_key, 0, -1)
    
    for _, subtask_id in ipairs(subtasks) do
        deleted_count = deleted_count + soft_delete_recursive(subtask_id, deleted_at)
    end
    
    return deleted_count
end

local total_deleted = 0
for i = 1, #ARGV - 1 do
    total_deleted = total_deleted + soft_delete_recursive(ARGV[i], ARGV[#ARGV])
end

return total_deleted
"""



GET_USER_TASKS_SCRIPT = """
local user_id = ARGV[1]
local user_active_key = 'user:' .. user_id .. ':tasks'
local user_completed_key = 'user:' .. user_id .. ':tasks:completed'

-- Get all active and completed task IDs
local active_ids = redis.call('ZRANGE', user_active_key, 0, -1)
local completed_ids = redis.call('ZRANGE', user_completed_key, 0, -1)

-- Combine all task IDs
local all_task_ids = {}
for _, id in ipairs(active_ids) do
    table.insert(all_task_ids, id)
end
for _, id in ipairs(completed_ids) do
    table.insert(all_task_ids, id)
end

-- Fetch all task data
local tasks = {}
for _, task_id in ipairs(all_task_ids) do
    local task_key = 'task:' .. task_id
    local task_data = redis.call('HGETALL', task_key)
    
    if #task_data > 0 then
        table.insert(tasks, task_data)
    end
end

return tasks
"""

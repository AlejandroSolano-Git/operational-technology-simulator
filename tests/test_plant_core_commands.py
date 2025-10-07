from plant.plant_core.commands import Command, CommandType, CommandQueue

def test_queue_order_and_peek_pop_clear():
    q = CommandQueue()
    q.push(Command(CommandType.START, t=1.0, source="hmi"))
    q.push(Command(CommandType.STOP, t=2.0, source="hmi"))
    # peek does not remove
    top = q.peek(); assert top and top.type == CommandType.START
    # pop removes in FIFO order
    c1 = q.pop(); assert c1.type == CommandType.START
    c2 = q.pop(); assert c2.type == CommandType.STOP
    assert q.pop() is None
    # clear is idempotent
    q.clear; assert q.pop() is None

def test_debounce_blocks_bursts_within():
    q = CommandQueue(debounce_s=0.5)
    # First push always allowed
    ok1 = q.push(Command(CommandType.START, t=10.0))
    # Second within 0.5s rejected
    ok2 = q.push(Command(CommandType.STOP, t=10.3))
    # Next after window accepted
    ok3 = q.push(Command(CommandType.STOP, t=10.6))
    assert ok1 is True and ok2 is False and ok3 is True
    # Only two should be in queue (t=10.0 and 1= 10.6)
    c1 = q.pop(); c2 = q.pop(); c3 = q.pop()
    assert c1.type == CommandType.START
    assert c2.type == CommandType.STOP
    assert c3 is None

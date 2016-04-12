from __future__ import division

import stack
from stack import next_instruction, eval_program, Instr

import pytest


def test_unicode_sigil():
    for sigil in Instr.sigil_to_op:
        assert Instr(sigil) == Instr(Instr.sigil_to_op[sigil])


def test_parse():
    expected = [Instr('push', [1]), Instr('pop'), Instr('swap')]
    # Any mix of semicolons and newlines should work
    assert list(stack.parse_program('push 1\npop\nswap')) == expected
    assert list(stack.parse_program('push 1; pop; swap')) == expected
    assert list(stack.parse_program('push 1; pop\nswap')) == expected
    # Spaces shouldn't matter for semicolons
    assert list(stack.parse_program('push 1 ;pop;  swap')) == expected
    # And empty instructions should be skipped
    assert list(stack.parse_program('push 1 ;;; pop\n;\nswap')) == expected


def test_parse_unicode():
    for sigil in Instr.sigil_to_op:
        instruction = next(stack.parse_program(sigil))
        assert instruction == Instr(Instr.sigil_to_op[sigil])


def test_next_instruction():
    program = next_instruction("push 1; pop; swap;")
    assert next(program) == "push 1"
    assert next(program) == "pop"
    assert next(program) == "swap"
    with pytest.raises(StopIteration):
        next(program)


def test_push_and_pop():
    assert eval_program("push 1; push 2; push 3;") == [1, 2, 3]
    assert eval_program("push 2; pop") == []
    with pytest.raises(IndexError):
        # IDEA: poping an empty list does nothing instead of index error?
        eval_program("pop")


def test_simple_operators():
    assert eval_program("push 10; push 20; add;") == [30]
    assert eval_program("push 10; push 5; subtract;") == [5]
    assert eval_program("push 10; push 20; subtract;") == [-10]
    assert eval_program("push 10; push 0; multiply;") == [0]
    assert eval_program("push 10; push 10; multiply;") == [100]
    assert eval_program("push 10; push 2; divide") == [5.0]
    assert eval_program("push 3; push 2; divide") == [1.5]
    with pytest.raises(IndexError):
        assert eval_program("push 1; add")
        assert eval_program("subtract; push 1")
        assert eval_program("push 1; push 2; pop; multiply")
        assert eval_program("divide")
    with pytest.raises(ZeroDivisionError):
        # IDEA: division by zero pushes nothing? halts program? pushes zero?
        assert eval_program("push 1; push 0; divide")


def test_float_division():
    assert eval_program("push 5; push 2; divide") == [2.5]
    assert eval_program("push 4; push 5; divide") == [0.8]
    assert eval_program("push 1; push 100; divide") == [0.01]


def test_complex_operators():
    program = "push 2; push 3; push 5; add; multiply"
    assert eval_program(program) == [2 * (3 + 5)]
    program = "push 36; push 24; push 6; divide; divide;"
    assert eval_program(program) == [36 / (24 / 6)]
    program = "push 10; push 4; subtract; push 6; push 2; subtract; multiply"
    assert eval_program(program) == [(10 - 4) * (6 - 2)]


def test_swap():
    assert eval_program("push 1; swap 0") == [1]
    assert eval_program("push 1; push 2; swap") == [2, 1]
    assert eval_program("push 1; push 2; swap 1") == [2, 1]
    assert eval_program("push 1; push 2; push 3; swap") == [1, 3, 2]
    assert eval_program("push 1; push 2; push 3; push 4; swap 3;") == [
        4, 2, 3, 1, ]
    with pytest.raises(IndexError):
        assert eval_program("swap")
        assert eval_program("push 1; swap")
        assert eval_program("push 1; push 2; swap 2")
        assert eval_program("push 1; push 2; push 3; swap 3")


def test_dup():
    assert eval_program("push 1; dup 0") == [1]
    assert eval_program("push 1; dup") == [1, 1]
    assert eval_program("push 1; dup 1") == [1, 1]
    assert eval_program("push 1; push 2; dup 2") == [1, 2, 1, 2]
    assert eval_program("push 1; dup; push 2; dup 3") == [1, 1, 2, 1, 1, 2]
    with pytest.raises(IndexError):
        # Should duping an empty stack be an error?
        # It technially duplicates the top element, which is nothing.
        assert eval_program("dup")
        assert eval_program("push 1; dup 2")

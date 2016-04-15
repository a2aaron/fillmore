# -*- coding: utf-8 -*-
from __future__ import division

import stack
from stack import eval_program, Instr

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


def test_push_and_pop():
    assert eval_program("push 1; push 2; push 3;") == [1, 2, 3]
    assert eval_program("push 2; pop") == []
    with pytest.raises(IndexError):
        # IDEA: popping an empty list does nothing instead of index error?
        eval_program("pop")


def test_simple_operators():
    assert eval_program("push 10; push 20; add;") == [30]
    assert eval_program("push 10; push 5; sub;") == [5]
    assert eval_program("push 10; push 20; sub;") == [-10]
    assert eval_program("push 10; push 0; mul;") == [0]
    assert eval_program("push 10; push 10; mul;") == [100]
    assert eval_program("push 10; push 2; div") == [5.0]
    assert eval_program("push 3; push 2; div") == [1.5]
    assert eval_program("push 4; push 4; pow") == [4**4]
    with pytest.raises(IndexError):
        assert eval_program("push 1; add")
    with pytest.raises(IndexError):
        assert eval_program("sub; push 1")
    with pytest.raises(IndexError):
        assert eval_program("push 1; push 2; pop; mul")
    with pytest.raises(IndexError):
        assert eval_program("div")
    with pytest.raises(ZeroDivisionError):
        # IDEA: division by zero pushes nothing? halts program? pushes zero?
        assert eval_program("push 1; push 0; div")


def test_float_division():
    assert eval_program("push 5; push 2; div") == [2.5]
    assert eval_program("push 4; push 5; div") == [0.8]
    assert eval_program("push 1; push 100; div") == [0.01]


def test_complex_operators():
    program = "push 2; push 3; push 5; add; mul"
    assert eval_program(program) == [2 * (3 + 5)]
    program = "push 36; push 24; push 6; div; div;"
    assert eval_program(program) == [36 / (24 / 6)]
    program = "push 10; push 4; sub; push 6; push 2; sub; mul"
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
    with pytest.raises(IndexError):
        assert eval_program("push 1; swap")
    with pytest.raises(IndexError):
        assert eval_program("push 1; push 2; swap 2")
    with pytest.raises(IndexError):
        assert eval_program("push 1; push 2; push 3; swap 3")


def test_dup():
    assert eval_program("push 1; dup 0") == [1]
    assert eval_program("push 1; dup") == [1, 1]
    assert eval_program("push 1; dup 1") == [1, 1]
    assert eval_program("push 1; push 2; dup 2") == [1, 2, 1, 2]
    assert eval_program("push 1; dup; push 2; dup 3") == [1, 1, 2, 1, 1, 2]
    with pytest.raises(IndexError):
        # Cannot duplicate the top element, since there is no top element
        assert eval_program("dup")
    with pytest.raises(IndexError):
        assert eval_program("push 1; dup 2")


def test_quiet():
    expected = [Instr('div', prefix=[]), Instr('add', prefix=['quiet'])]
    assert list(stack.parse_program('div; quiet add')) == expected

    assert eval_program("push 3; push 5; quiet add") == [3, 5, 8]
    assert eval_program("push 3; push 5; quiet mul") == [3, 5, 15]
    assert eval_program("push 3; push 5; quiet sub") == [3, 5, -2]
    assert eval_program("push 3; push 5; quiet div") == [3, 5, 0.6]
    assert eval_program("push 3; push 5; quiet pow") == [3, 5, 3**5]


def test_negation():
    assert eval_program("push 1; not;") == [0]
    assert eval_program("push -1; not;") == [0]
    assert eval_program("push 0; not;") == [1]
    assert eval_program("push 3; push 7; push 0; not;") == [3, 7, 1]
    assert eval_program("push 1; quiet not;") == [1, 0]
    assert eval_program("push 0; quiet not;") == [0, 1]
    with pytest.raises(IndexError):
        # Cannot negate top element since there isn't a top element
        assert eval_program('not')


def test_equality():
    assert eval_program("push 0; push 0; eq") == [1]
    assert eval_program("push 1.0; push 1.0; =") == [1]
    assert eval_program("push 2.0; push 2; =") == [1]
    assert eval_program("push -1; push -1; eq") == [1]
    assert eval_program("push 3; push 5; eq") == [0]
    assert eval_program("push 4; push 4; quiet eq") == [4, 4, 1]
    assert eval_program("push 3; push 5; quiet eq") == [3, 5, 0]
    with pytest.raises(IndexError):
        assert eval_program("eq")
    with pytest.raises(IndexError):
        assert eval_program("push 1; eq")


def test_inequality():
    assert eval_program("push 5; push 7; lt") == [1]
    assert eval_program("push 5; push 7; le") == [1]
    assert eval_program("push 3; push 3; le") == [1]
    assert eval_program("push -1; push 0; quiet <") == [-1, 0, 1]
    assert eval_program("push 5.1; push 5.0; quiet >=") == [5.1, 5.0, 1]
    assert eval_program("push -3; push 27; <=") == [1]
    assert eval_program("push 7; push 5; gt") == [1]
    assert eval_program("push 7; push 5; ge") == [1]
    assert eval_program("push 3; push 3; ge") == [1]
    with pytest.raises(IndexError):
        assert eval_program(">")
    with pytest.raises(IndexError):
        assert eval_program("push 1; ≤")

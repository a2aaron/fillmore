# -*- coding: utf-8 -*-
from __future__ import division

import stack
from stack import eval_program, parse_program, Instr

import pytest


def test_parse():
    expected = [Instr('push', [1]), Instr('pop'), Instr('swap')]
    # Any mix of semicolons and newlines should work
    assert list(parse_program('push 1\npop\nswap')) == expected
    assert list(parse_program('push 1; pop; swap')) == expected
    assert list(parse_program('push 1; pop\nswap')) == expected
    # Spaces shouldn't matter for semicolons
    assert list(parse_program('push 1 ;pop;  swap')) == expected
    # And empty instructions should be skipped
    assert list(parse_program('push 1 ;;; pop\n;\nswap')) == expected
    with pytest.raises(ValueError):
        list(stack.parse_program('horp; push 0'))


def test_parse_quiet():
    expected = [Instr('div', prefix=[]), Instr('add', prefix=['quiet'])]
    assert list(parse_program('div; quiet add')) == expected
    expected = Instr('jump', prefix=['quiet'])
    assert next(parse_program('quiet jump')) == expected
    for quiet in ['#', '♯', 'quiet']:
        expected = [Instr('jump', prefix=['quiet'])]
        assert list(parse_program(quiet + ' jump')) == expected


def test_parse_invalid():
    programs = ['quiet ad 6', 
                'pop push',
                'push 1 add',
                '1',
                'not real'
                'invalid add'
                ]
    for program in programs:
        with pytest.raises(ValueError):    
            next(parse_program(program))


def test_is_well_formed():
    valid_cases = ['@label',
                   'add',
                   'jump @label',
                   'add @label',
                   'quiet not',
                   'cond quiet not',
                   'cond quiet jump @label',
                   'cond qcond jump']
    for case in valid_cases:
        case = case.strip().split()
        assert stack.is_well_formed(case) == True

    invalid_cases = ['@label jump',
                     'jump quiet',
                     'this should not work',
                     'cond add quiet',
                     'quiet quiet add',
                     'quiet cond',
                     '@label @label',
                     'sub add',
                     'bad add'
                     'eq bad']
    for case in invalid_cases:
        case = case.strip().split()
        assert stack.is_well_formed(case) == False


def test_argument_errors():
    with pytest.raises(ValueError):
        list(stack.parse_program('push'))

    int_arg = ['jump', 'dup', 'swap']
    for op in int_arg:
        with pytest.raises(ValueError):
            list(stack.parse_program(op + ' 0.5'))

    no_arg = ['pop', 'add', 'sub', 'mul', 'div', 'pow', 'eq',
              'lt', 'gt', 'le', 'ge', 'not']
    for op in no_arg:
        with pytest.raises(ValueError):
            list(stack.parse_program(op + ' 1'))

    one_arg = ['dup', 'swap', 'jump']
    for op in no_arg + one_arg:
        with pytest.raises(ValueError):
            list(stack.parse_program(op + ' 1 1'))


def test_push_and_pop():
    assert eval_program('push 1; push 2; push 3;') == [1, 2, 3]
    assert eval_program('push 2; pop') == []
    with pytest.raises(IndexError):
        eval_program('pop')


def test_simple_operators():
    assert eval_program('push 10; push 20; add;') == [30]
    assert eval_program('push 10; push 5; sub;') == [5]
    assert eval_program('push 10; push 20; sub;') == [-10]
    assert eval_program('push 10; push 0; mul;') == [0]
    assert eval_program('push 10; push 10; mul;') == [100]
    assert eval_program('push 10; push 2; div') == [5.0]
    assert eval_program('push 3; push 2; div') == [1.5]
    assert eval_program('push 4; push 4; pow') == [4**4]
    with pytest.raises(IndexError):
        eval_program('push 1; add')
    with pytest.raises(IndexError):
        eval_program('sub; push 1')
    with pytest.raises(IndexError):
        eval_program('push 1; push 2; pop; mul')
    with pytest.raises(IndexError):
        eval_program('div')
    with pytest.raises(ZeroDivisionError):
        eval_program('push 1; push 0; div')


def test_float_division():
    assert eval_program('push 5; push 2; div') == [2.5]
    assert eval_program('push 4; push 5; div') == [0.8]
    assert eval_program('push 1; push 100; div') == [0.01]


def test_complex_operators():
    program = 'push 2; push 3; push 5; add; mul'
    assert eval_program(program) == [2 * (3 + 5)]
    program = 'push 36; push 24; push 6; div; div;'
    assert eval_program(program) == [36 / (24 / 6)]
    program = 'push 10; push 4; sub; push 6; push 2; sub; mul'
    assert eval_program(program) == [(10 - 4) * (6 - 2)]


def test_swap():
    assert eval_program('push 1; swap 0') == [1]
    assert eval_program('push 1; push 2; swap') == [2, 1]
    assert eval_program('push 1; push 2; swap 1') == [2, 1]
    assert eval_program('push 1; push 2; push 3; swap') == [1, 3, 2]
    code = 'push 1; push 2; push 3; push 4; swap 3;'
    assert eval_program(code) == [4, 2, 3, 1]
    with pytest.raises(IndexError):
        eval_program('swap')
    with pytest.raises(IndexError):
        eval_program('push 1; swap')
    with pytest.raises(IndexError):
        eval_program('push 1; push 2; swap 2')
    with pytest.raises(IndexError):

        eval_program('push 1; push 2; push 3; swap 3')


def test_dup():
    assert eval_program('push 1; dup 0') == [1]
    assert eval_program('push 1; dup') == [1, 1]
    assert eval_program('push 1; dup 1') == [1, 1]
    assert eval_program('push 1; push 2; dup 2') == [1, 2, 1, 2]
    assert eval_program('push 1; dup; push 2; dup 3') == [1, 1, 2, 1, 1, 2]
    with pytest.raises(IndexError):
        # Cannot duplicate the top element, since there is no top element
        eval_program('dup')
    with pytest.raises(IndexError):
        eval_program('push 1; dup 2')


def test_quiet():
    assert eval_program('push 3; push 5; quiet add') == [3, 5, 8]
    assert eval_program('push 3; push 5; quiet mul') == [3, 5, 15]
    assert eval_program('push 3; push 5; quiet sub') == [3, 5, -2]
    assert eval_program('push 3; push 5; quiet div') == [3, 5, 0.6]
    assert eval_program('push 3; push 5; quiet pow') == [3, 5, 3**5]


def test_negation():
    assert eval_program('push 1; not;') == [0]
    assert eval_program('push -1; not;') == [0]
    assert eval_program('push 0; not;') == [1]
    assert eval_program('push 3; push 7; push 0; not;') == [3, 7, 1]
    assert eval_program('push 5; quiet not;') == [5, 0]
    assert eval_program('push 0; quiet not;') == [0, 1]
    with pytest.raises(IndexError):
        # Cannot negate top element since there isn't a top element
        eval_program('not')


def test_equality():
    assert eval_program('push 0; push 0; eq') == [1]
    assert eval_program('push 1.0; push 1.0; =') == [1]
    assert eval_program('push 2.0; push 2; =') == [1]
    assert eval_program('push -1; push -1; eq') == [1]
    assert eval_program('push 3; push 5; eq') == [0]
    assert eval_program('push 4; push 4; quiet eq') == [4, 4, 1]
    assert eval_program('push 3; push 5; quiet eq') == [3, 5, 0]
    with pytest.raises(IndexError):
        eval_program('eq')
    with pytest.raises(IndexError):
        eval_program('push 1; eq')


def test_inequality():
    assert eval_program('push 5; push 7; lt') == [1]
    assert eval_program('push 5; push 7; le') == [1]
    assert eval_program('push 3; push 3; le') == [1]
    assert eval_program('push -1; push 0; quiet <') == [-1, 0, 1]
    assert eval_program('push 5.1; push 5.0; quiet >=') == [5.1, 5.0, 1]
    assert eval_program('push -3; push 27; <=') == [1]
    assert eval_program('push 7; push 5; gt') == [1]
    assert eval_program('push 7; push 5; ge') == [1]
    assert eval_program('push 3; push 3; ge') == [1]
    with pytest.raises(IndexError):
        eval_program('>')
    with pytest.raises(IndexError):
        eval_program('push 1; ≤')

def test_float_comparision():
    assert eval_program('push 3; push 3; eq;') == [1.0]
    assert eval_program('push 3; push 2; ge; push 2.5; mul;') == [2.5]
    assert eval_program('push 1; push 1; eq; dup; quiet +; ÷') == [1.0, 0.5]


@pytest.mark.timeout(1)
def test_jump():
    # It should be possible to jump one past the end of the code, but no more
    assert eval_program('jump 1;') == []
    with pytest.raises(IndexError):
        eval_program('jump 2;')
    assert eval_program('jump 2; push 1') == []
    assert eval_program('jump 1; push 1') == [1]
    assert eval_program('jump 3; push 9; jump 2; jump -2') == [9]
    # Jumping before the first instruction shouldn't be valid either
    with pytest.raises(IndexError):
        eval_program('jump -10')
    with pytest.raises(IndexError):
        eval_program('jump -1; jump 0')

@pytest.mark.timeout(1)
def test_dynamic_jump():
    # A jump with no argument should jump based on the top of the stack
    assert eval_program('push 2; jump; push 1') == []
    assert eval_program('jump 3; push 9; jump 3; push -3; jump') == [9]
    assert eval_program('push 1; jump') == []
    assert eval_program('push 1; quiet jump') == [1]
    with pytest.raises(IndexError):
        eval_program('push 2; jump')
    with pytest.raises(IndexError):
        eval_program('push -2; jump; jump 0')


@pytest.mark.timeout(1)
def test_jump_labels():
    # A jump label should be converted into relative jumps at parse time.
    expected = [Instr('push', [1]), Instr('push', [2]), Instr('to', [0])]
    program = '@start\npush 1; push 2; jump @start'
    assert list(parse_program(program)) == expected

    # Multiple jump labels should work.


def test_cond():
    # cond is a prefix that only allows the next instruction
    # to execute if the top stack value is not zero.
    # It pops the top value even if the condition isn't met.
    assert eval_program('push 1; cond push 2') == [2]
    assert eval_program('push 0; cond push 2') == []

    # Floats and negatives do trigger the conditional
    assert eval_program('push 1; push 2; div; cond push 2') == [2]
    assert eval_program('push 0; push 2; div; cond push 2') == []
    assert eval_program('push -1; cond push 2') == [2]
    # Since cond pops the stack, it's an error to pop an empty stack
    with pytest.raises(IndexError):
        eval_program('cond push 2')
    with pytest.raises(ValueError):
        eval_program('cond')

    # It's not an error to TRY to conditionally execute
    # even if the stack is too small, but it is an error
    # if that instruction does actually execute.
    assert eval_program('push 0; cond add') == []
    with pytest.raises(IndexError):
        eval_program('push 1; cond add')

    # "quiet cond op" will execute the op quietly.
    # It is identical to "cond quiet op"
    assert eval_program('push 1; push 2; push 100; quiet cond add')  == [1, 2, 3]
    assert eval_program('push 3; push 2; cond quiet not')  == [3, 0]

def test_qcond():
    # Similar to cond, qcond will execute the next instruction
    # if the top stack on the value is not zero.
    # However it does not pop the top value.
    # Effectively, qcond "fake pops" the top value
    # then does the instruction, and finially repushes the inital value.
    assert eval_program('push 1; push 2; push 3; qcond push 4') == [1, 2, 4, 3]
    assert eval_program('push 1; push 2; push 0; qcond push 4') == [1, 2, 0]
    # You can also use it with the quiet prefix
    # Note that the operation will use the items below the top element
    assert eval_program('push 10; push 20; push 1; ?? *') == [200, 1]
    assert eval_program('push 10; push 20; push 1; ?? # add') == [10, 20, 30, 1]
    # Note that you can't use cond and qcond in the same instruction.
    with pytest.raises(ValueError):
        list(parse_program('cond qcond add'))

@pytest.mark.timeout(1)
def test_fibonacci():
    # Has the nth fibonacci term at the top of the stack
    # TODO: test against different fibonacci inputs.
    # (0 = 0th term)
    program = '''
    push 1
    push 0
    push 6
    @setup
    swap 2
    @next_fib
    dup
    swap 2
    add
    @decrement_n
    swap 2
    push -1
    add
    @check_for_zero
    quiet not
    push 1
    add
    jump
    jump @setup
    jump @end
    @end
    swap 2
    pop
    swap
    pop'''
    assert eval_program(program) == [8]

@pytest.mark.timeout(1)
def test_absolute_jump():
    # An absolute jump will jump to the instruction number
    # reguardless of where the jump is placed. Instructions start at 0.
    assert eval_program('to 2; push 2; push 3; push 4') == [3, 4]
    # If no argument is specified, pop the top element.
    # If quiet is specified, don't discard the top element.
    assert eval_program('push 2; to; push 5; push 6') == [5, 6]
    assert eval_program('push 2; quiet to; push 5; push 6') == [2, 5, 6]

@pytest.mark.timeout(1)
def test_illegal_jump():
    # Attempting to jump before the start
    # or after the end of a program is an error.
    with pytest.raises(IndexError):
        eval_program('to -1; push 1; push 2')
    with pytest.raises(IndexError):
        eval_program('to 4; push 1')
    # Whole number floats should be jumpable,
    assert eval_program('push 12; push 3; div; quiet to; push 1; push 2') == [4.0, 1, 2]
    # but shouldn't be able to jump to floats,
    with pytest.raises(TypeError):
        eval_program('push 4; push 5; div; to')


def test_bad_labels():
    # A missing jump label is an error.
    with pytest.raises(ValueError):
        code = 'jump @missing_label'
        list(parse_program(code))
    # Two labels with the same name is an error.
    with pytest.raises(ValueError):
        code = '@label; push 2; @label; add'
        list(parse_program(code))
    # Multiple jumps to the same label are fine however.
    code = '@label; push 2; jump @label; jump @label'
    list(parse_program(code))


def test_bad_prefixes():
    # A prefix without an instruction is an error.
    with pytest.raises(ValueError):
       list(parse_program('quiet'))
    with pytest.raises(ValueError):
       list(parse_program('cond'))
    # Duplicated prefixes are not allowed.
    with pytest.raises(ValueError):
        list(parse_program('quiet quiet push 1'))
    # The prefix must come before the instruction.
        list(parse_program('not cond'))

def test_label_with_instruction():
    # Labels before an instruction are an error.
    with pytest.raises(ValueError):
        list(parse_program('@label; @label add;'))
    with pytest.raises(ValueError):
        list(parse_program('@label; @label jump;'))
    # If there is a label and the opcode isn't jump or to, then that's an error.
    with pytest.raises(ValueError):
        list(parse_program('@label; add @label;'))
    # Two labels on the same line is an error.
    with pytest.raises(ValueError):
        list(parse_program('@label; jump @label @label;'))
    list(parse_program('@label; jump @label'))
    list(parse_program('@label; to @label'))


def test_nop():
    assert eval_program('nop') == []
    assert eval_program('∅') == []


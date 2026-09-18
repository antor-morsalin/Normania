import random
import pytest
from Data.arucoMap import ARUCO_TO_TOKEN
from Data.syntaxMap import SYNTAX_MAP
from Parsing.parse import Parser, ProgramValidationError
from main import execute_python

IDS = {token: marker for marker, token in ARUCO_TO_TOKEN.items()}


def board(*rows):
    result = [[IDS[token] if isinstance(token, str) else token for token in row] for row in rows]
    return [row + [None] * (5 - len(row)) for row in result] + [[None] * 5 for _ in range(6 - len(result))]


def run(matrix):
    parser = Parser()
    code = parser.convert_to_python(parser.create_statements(matrix))
    return code, execute_python(code, parser.line_map)


USER_MATRIX = [[2, 18, 12, None, None], [32, 2, 21, None, None],
               [35, None, None, None, None], [34, None, None, None, None],
               [35, 42, None, None, None], [None] * 5]


def test_exact_user_crash_is_row_error():
    with pytest.raises(ProgramValidationError, match='Row 3: SHOW needs exactly one value'):
        run(USER_MATRIX)


def test_exact_user_loop_when_all_markers_visible():
    matrix = [r.copy() for r in USER_MATRIX]
    matrix[2][1] = 41
    code, output = run(matrix)
    assert code == "c = 4\nfor _ in range(c):\n    print('KEEP TRYING')\nprint('YOU CAN DO IT')"
    assert output == 'KEEP TRYING\n' * 4 + 'YOU CAN DO IT\n'


@pytest.mark.parametrize('value,expected', [('6', 'GREAT JOB\n'), ('2', 'KEEP TRYING\n')])
def test_if_otherwise_branches(value, expected):
    _, output = run(board(['X','IS',value], ['IF','X','MORE THAN','5','THEN'],
                          ['SHOW','GREAT JOB'], ['OTHERWISE'], ['SHOW','KEEP TRYING'], ['END']))
    assert output == expected


@pytest.mark.parametrize('value,expected', [('1', 'GREAT JOB\n'), ('2', 'KEEP TRYING\n')])
def test_otherwise_after_end_attaches_to_the_if(value, expected):
    matrix = board(['IF',value,'IS','1','THEN'], ['SHOW','GREAT JOB'], ['END'],
                   ['OTHERWISE'], ['SHOW','KEEP TRYING'], ['END'])
    parser = Parser()
    code = parser.convert_to_python(parser.create_statements(matrix))
    assert code == f"if {value} == 1:\n    print('GREAT JOB')\nelse:\n    print('KEEP TRYING')"
    assert execute_python(code, parser.line_map) == expected
    assert parser.line_map == {1: 1, 2: 2, 3: 4, 4: 5}


def test_otherwise_after_end_runtime_error_keeps_physical_row():
    _, output = run(board(['IF','1','IS','2','THEN'], ['SHOW','HELLO'], ['END'],
                         ['OTHERWISE'], ['SHOW','X'], ['END']))
    assert 'Row 5: X has no value' in output


@pytest.mark.parametrize('rows,match', [
    ([['IF','1','IS','2','THEN'],['SHOW','HELLO'],['END'],['SHOW','HELLO'],['OTHERWISE']],
     'Row 5: OTHERWISE needs an open IF'),
    ([['REPEAT','2','TIMES'],['SHOW','HELLO'],['END'],['OTHERWISE']],
     'Row 4: OTHERWISE needs an open IF'),
    ([['IF','1','IS','2','THEN'],['SHOW','HELLO'],['END'],['OTHERWISE'],['SHOW','HELLO']],
     'IF needs a matching END'),
    ([['IF','1','IS','2','THEN'],['SHOW','HELLO'],['END'],['OTHERWISE'],['END']],
     'OTHERWISE .*needs an instruction'),
])
def test_closed_if_does_not_hide_invalid_scope(rows, match):
    with pytest.raises(ProgramValidationError, match=match):
        run(board(*rows))


@pytest.mark.parametrize('rows,match', [
    ([['C','4']], 'Row 1: C needs IS'),
    ([['IF','X','MORE THAN','5'],['SHOW','HELLO'],['END']], 'Row 1: IF needs THEN'),
    ([['REPEAT']], 'Row 1: Use REPEAT'),
    ([['REPEAT','3']], 'Row 1: Use REPEAT'),
    ([['SHOW','HELLO','OTHERWISE']], 'Row 1: SHOW needs exactly one'),
    ([['IF','X','IS','THEN']], 'Row 1: Use IF'),
    ([['X','IS','2','PLUS']], 'Row 1: Use X IS'),
    ([['X','IS','1','0']], 'Row 1: Use X IS'),
    ([['END']], 'Row 1: END has no open'),
    ([['OTHERWISE']], 'Row 1: OTHERWISE needs an open IF'),
    ([['IF','3','IS','3','THEN'],['SHOW','HELLO']], 'Row 1: IF needs a matching END'),
    ([['IF','3','IS','3','THEN'],['END']], 'Row 2: IF .*needs an instruction'),
    ([['IF','3','IS','3','THEN'],['OTHERWISE'],['END']], 'Row 2: IF .*no instruction'),
    ([['IF','3','IS','3','THEN'],['SHOW','HELLO'],['OTHERWISE'],['END']], 'Row 4: OTHERWISE .*needs an instruction'),
    ([['IF','3','IS','3','THEN'],['SHOW','HELLO'],['OTHERWISE'],['SHOW','HELLO'],['OTHERWISE'],['END']], 'Row 5: IF .*already has OTHERWISE'),
    ([['REPEAT','3','TIMES'],['SHOW','HELLO'],['OTHERWISE'],['END']], 'Row 3: Close REPEAT'),
    ([['END','SHOW','HELLO']], 'Row 1: END must be alone'),
    ([['THEN']], 'Row 1: An instruction cannot start with THEN'),
])
def test_invalid_rows_and_scopes(rows, match):
    with pytest.raises(ProgramValidationError, match=match):
        run(board(*rows))


def test_repeated_tokens_and_gaps_are_preserved():
    matrix = board(['X','IS','3'], ['IF','X','IS','X','THEN'], ['SHOW',None,'X'], ['END'])
    _, output = run(matrix)
    assert output == '3\n'


def test_nested_scopes_close_in_order():
    _, output = run(board(['REPEAT','2','TIMES'], ['REPEAT','3','TIMES'],
                         ['SHOW','HELLO'], ['END'], ['END'], ['SHOW','GREAT JOB']))
    assert output == 'HELLO\n' * 6 + 'GREAT JOB\n'


def test_nested_if_and_post_end_output():
    _, output = run(board(['IF','1','IS','1','THEN'], ['IF','2','IS','2','THEN'],
                         ['SHOW','HELLO'], ['END'], ['END'], ['SHOW','GREAT JOB']))
    assert output == 'HELLO\nGREAT JOB\n'


@pytest.mark.parametrize('operator,expected', [('AND',''),('OR','HELLO\n')])
def test_boolean_conditions(operator, expected):
    _, output = run(board(['CONDITION1','IS','3','IS','3'], ['CONDITION2','IS','3','IS NOT','3'],
                         ['IF','CONDITION1',operator,'CONDITION2','THEN'], ['SHOW','HELLO'], ['END']))
    assert output == (expected or 'Program completed with no output.')


@pytest.mark.parametrize('operator,result', [('PLUS','7'),('MINUS','1'),('TIMES','12'),('DIVIDED BY','1.3333333333333333')])
def test_contextual_arithmetic(operator, result):
    _, output = run(board(['X','IS','4',operator,'3'], ['SHOW','X']))
    assert output == result + '\n'


@pytest.mark.parametrize('operator,expected', [('IS',False),('IS NOT',True),('MORE THAN',True),('LESS THAN',False),('AT LEAST',True),('AT MOST',False)])
def test_comparisons(operator, expected):
    _, output = run(board(['IF','4',operator,'3','THEN'], ['SHOW','HELLO'], ['END']))
    assert output == ('HELLO\n' if expected else 'Program completed with no output.')


def test_all_physical_tokens_have_syntax():
    assert set(ARUCO_TO_TOKEN.values()) <= SYNTAX_MAP.keys()
    assert run(board(['SHOW','MY NAME IS']))[1] == 'MY NAME IS\n'


def test_physical_row_numbers_survive_empty_rows():
    with pytest.raises(ProgramValidationError, match='Row 4: SHOW'):
        run(board([], [], [], ['SHOW']))
    _, output = run(board([], [], ['SHOW','X']))
    assert 'Row 3: X has no value' in output


@pytest.mark.parametrize('rows,message', [
    ([['X','IS','4','DIVIDED BY','0']], 'Row 1: A number cannot be divided by zero'),
    ([['X','IS','3','DIVIDED BY','2'],['REPEAT','X','TIMES'],['SHOW','HELLO'],['END']], 'Row 2: REPEAT needs'),
    ([['X','IS','0','MINUS','1'],['REPEAT','X','TIMES'],['SHOW','HELLO'],['END']], 'Row 2: REPEAT needs'),
    ([['X','IS','HELLO'],['X','IS','X','TIMES','3']], 'Row 2: Arithmetic'),
    ([['X','IS','HELLO'],['IF','X','MORE THAN','2','THEN'],['SHOW','HELLO'],['END']], 'Row 2: Arithmetic'),
])
def test_runtime_errors_refer_to_board(rows, message):
    assert message in run(board(*rows))[1]


def test_zero_loop_does_not_execute_body():
    assert run(board(['REPEAT','0','TIMES'],['SHOW','HELLO'],['END'],['SHOW','GREAT JOB']))[1] == 'GREAT JOB\n'


def test_execution_limits_and_trace_cleanup():
    import sys
    original = sys.gettrace()
    code = "for _ in range(99999):\n    print('HELLO')"
    assert 'repeats too much' in execute_python(code, max_steps=5)
    assert 'output is too long' in execute_python(code, output_limit=10)
    assert sys.gettrace() is original
    assert execute_python("print('HELLO')") == 'HELLO\n'


def test_malformed_marker_matrices_never_raise_index_error():
    rng = random.Random(1909)
    marker_ids = list(ARUCO_TO_TOKEN) + [None, None, None, 99]
    for _ in range(2500):
        matrix = [[rng.choice(marker_ids) for _ in range(5)] for _ in range(6)]
        try:
            parser = Parser()
            code = parser.convert_to_python(parser.create_statements(matrix))
            compile(code, '<test>', 'exec')
        except ProgramValidationError:
            pass


@pytest.mark.parametrize('matrix', [[[True]], [[1.2]], [[[]]], [[-1]], [[200]], [[1]*6], [[None]*5]*7])
def test_invalid_matrix_cells(matrix):
    with pytest.raises(ProgramValidationError):
        run(matrix)

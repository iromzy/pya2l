import ctypes
import math

import pytest

from .helpers.compu_method import *
from .helpers.helpers import get_unpack_format_from_a2l_datatype, get_byte_size_from_unpack_format
from .parser import A2lParser as Parser
from .parser_test import idents, strings, project_string_minimal, module, module_string_minimal, empty_string


@pytest.fixture()
def byte_order(request):
    return request.param


@pytest.fixture()
def values(request):
    return request.param


@pytest.mark.parametrize('datatype, unpack_format', [('UBYTE', 'B'),
                                                     ('SBYTE', 'b'),
                                                     ('UWORD', 'H'),
                                                     ('SWORD', 'h'),
                                                     ('ULONG', 'I'),
                                                     ('FLOAT32_IEEE', 'f'),
                                                     ('FLOAT64_IEEE', 'd')])
def test_get_unpack_format_from_a2l_datatype(datatype, unpack_format):
    assert get_unpack_format_from_a2l_datatype(datatype) == unpack_format


@pytest.mark.parametrize('unpack_format, byte_size', [('B', 1),
                                                      ('b', 1),
                                                      ('H', 2),
                                                      ('h', 2),
                                                      ('I', 4),
                                                      ('f', 4),
                                                      ('d', 8),
                                                      ('>B', 1),
                                                      ('<B', 1),
                                                      ('>Bh', 3),
                                                      ('<Bh', 3)])
def test_get_byte_size_from_unpack_format(unpack_format, byte_size):
    assert get_byte_size_from_unpack_format(unpack_format) == byte_size


@pytest.mark.parametrize('s', ['''
    /begin MODULE {ident} {string}
    /end MODULE'''])
@pytest.mark.parametrize('ident_string, ident_value', idents)
@pytest.mark.parametrize('string_string, string_value', strings)
def test_module_name(s, ident_string, ident_value, string_string, string_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(s.format(ident=ident_string,
                                                                     string=string_string, )).encode())
        assert Module(ast.PROJECT.MODULE[0]).name == ident_value


@pytest.mark.parametrize('module, byte_order, values', [
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('MSB_FIRST', 'big')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('BIG_ENDIAN', 'big')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('MSB_LAST', 'little')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('LITTLE_ENDIAN', 'little')),
    (['MOD_COMMON'], '{}', ('', 'little')),
    ([], '{}', ('', 'little'))], indirect=True)
def test_module_endianness(module, byte_order, values):
    with Parser() as p:
        ast = p.tree_from_a2l(module[0].format(byte_order.format(values[0])).encode())
        assert Module(ast.PROJECT.MODULE[0]).endianness == values[1]


@pytest.mark.parametrize('module, byte_order, values', [
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('MSB_FIRST', '>')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('BIG_ENDIAN', '>')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('MSB_LAST', '<')),
    (['MOD_COMMON', 'BYTE_ORDER'], 'BYTE_ORDER {}', ('LITTLE_ENDIAN', '<')),
    (['MOD_COMMON'], '{}', ('', '<')),
    ([], '{}', ('', '<'))], indirect=True)
def test_module_unpack_format(module, byte_order, values):
    with Parser() as p:
        ast = p.tree_from_a2l(module[0].format(byte_order.format(values[0])).encode())
        assert Module(ast.PROJECT.MODULE[0]).unpack_format == values[1]


@pytest.mark.parametrize('s', ['''
    /begin COMPU_METHOD {ident} {string} {enum_conversion_type} {string} {string} /end COMPU_METHOD'''])
@pytest.mark.parametrize('ident_string, ident_value', idents)
@pytest.mark.parametrize('string_string, string_value', strings)
@pytest.mark.parametrize('conversion_type_string, class_type', (
        pytest.param('TAB_INTP', CompuMethodTabIntp, id='TAB_INTP'),
        pytest.param('TAB_NOINTP', CompuMethodTabNoIntp, id='TAB_NOINTP'),
        pytest.param('TAB_VERB', CompuMethodTabVerb, id='TAB_VERB'),
        pytest.param('RAT_FUNC', CompuMethodRatFunc, id='RAT_FUNC'),
        pytest.param('FORM', CompuMethodForm, id='FORM')))
def test_compu_method_factory(s,
                              ident_string, ident_value,
                              string_string, string_value,
                              conversion_type_string, class_type):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(s.format(
            ident=ident_string,
            string=string_string,
            enum_conversion_type=conversion_type_string,
            formula=empty_string,
            coeffs=empty_string,
            compu_tab_ref=empty_string,
            ref_unit=empty_string))).encode())
        assert isinstance(compu_method_factory(Module(ast.PROJECT.MODULE[0]), ast.PROJECT.MODULE[0].COMPU_METHOD[0]),
                          class_type)


@pytest.mark.parametrize('s', ['''
    /begin COMPU_METHOD {name} {string} {enum_conversion_type} {format} {unit} /end COMPU_METHOD'''])
@pytest.mark.parametrize('name_string, name_value', idents)
@pytest.mark.parametrize('string_string, string_value', strings)
@pytest.mark.parametrize('conversion_type_string, class_type', (
        pytest.param('TAB_INTP', CompuMethodTabIntp, id='TAB_INTP'),
        pytest.param('TAB_NOINTP', CompuMethodTabNoIntp, id='TAB_NOINTP'),
        pytest.param('TAB_VERB', CompuMethodTabVerb, id='TAB_VERB'),
        pytest.param('RAT_FUNC', CompuMethodRatFunc, id='RAT_FUNC'),
        pytest.param('FORM', CompuMethodForm, id='FORM')))
@pytest.mark.parametrize('format_string, format_value', strings)
@pytest.mark.parametrize('unit_string, unit_value', strings)
def test_compu_method_properties(s,
                                 name_string, name_value,
                                 string_string, string_value,
                                 conversion_type_string, class_type,
                                 format_string, format_value,
                                 unit_string, unit_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(s.format(
            name=name_string,
            string=string_string,
            enum_conversion_type=conversion_type_string,
            format=format_string,
            unit=unit_string))).encode())
        assert class_type(Module(ast.PROJECT.MODULE[0]), ast.PROJECT.MODULE[0].COMPU_METHOD[0]).unit == unit_value
        assert class_type(Module(ast.PROJECT.MODULE[0]), ast.PROJECT.MODULE[0].COMPU_METHOD[0]).format == format_value
        assert class_type(Module(ast.PROJECT.MODULE[0]), ast.PROJECT.MODULE[0].COMPU_METHOD[0]).a2l_compu_method == \
               ast.PROJECT.MODULE[0].COMPU_METHOD[0]


@pytest.mark.parametrize('tab_intp, internal_value, physical_value', [((0, 0, 255, 255), 0, 0),
                                                                      ((0, 0, 255, 255), 1, 1),
                                                                      ((0, 0, 255, 255), 255, 255),
                                                                      ((1, 10, 2, 20), 1.5, 15),
                                                                      ((1, 10, 2, 20), 0, 10),
                                                                      ((1, 10, 2, 20), 3, 20),
                                                                      ((1, 10, 2, 20, 3, 40), 2.5, 30)])
def test_compu_method_tab_intp_internal_to_physical_conversion(tab_intp, internal_value, physical_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" TAB_INTP "" ""
        COMPU_TAB_REF ref
    /end COMPU_METHOD
    /begin COMPU_TAB ref ""
         TAB_INTP
         {int(len(tab_intp) / 2)}
         {" ".join([str(e) for e in tab_intp])}
    /end COMPU_TAB''')).encode())
        assert CompuMethodTabIntp(Module(ast.PROJECT.MODULE[0]),
                                  ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(
            internal_value) == physical_value


def test_compu_method_tab_intp_internal_to_physical_conversion_value_error():
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" TAB_INTP "" ""
        COMPU_TAB_REF ref
    /end COMPU_METHOD
    /begin COMPU_TAB _ref ""
         TAB_INTP
         1
         1 1
    /end COMPU_TAB''')).encode())
    with pytest.raises(ValueError) as excinfo:
        CompuMethodTabIntp(Module(ast.PROJECT.MODULE[0]),
                           ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(0)
    assert str(excinfo.value) == f'COMPU_TAB <ref> not found in MODULE <_>'


@pytest.mark.skip(reason="Not implemented")
def test_compu_method_tab_no_intp_internal_to_physical_conversion():
    pass


@pytest.mark.parametrize('tab_verb, internal_value, physical_value', [((0, '"A"'), 0, 'A'),
                                                                      ((0, '"A"', 1, '"B"'), 1, 'B'),
                                                                      ((0, '"A"', 1, '"B"', 2, '"C"'), 2, 'C'),
                                                                      ((0, '"A"', 1, '"B"', 2, '"C"'), 1, 'B')])
def test_compu_method_tab_verb_internal_to_physical_conversion(tab_verb, internal_value, physical_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" TAB_VERB "" ""
        COMPU_TAB_REF ref
    /end COMPU_METHOD
    /begin COMPU_VTAB ref ""
         TAB_VERB
         {int(len(tab_verb) / 2)}
         {" ".join([str(e) for e in tab_verb])}
    /end COMPU_VTAB''')).encode())
        assert CompuMethodTabVerb(Module(ast.PROJECT.MODULE[0]),
                                  ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(
            internal_value) == physical_value


def test_compu_method_tab_verb_internal_to_physical_conversion_index_error():
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" TAB_VERB "" ""
        COMPU_TAB_REF ref
    /end COMPU_METHOD
    /begin COMPU_VTAB ref ""
         TAB_VERB
         1
         0 "A"
    /end COMPU_VTAB''')).encode())
    with pytest.raises(IndexError) as excinfo:
        CompuMethodTabVerb(Module(ast.PROJECT.MODULE[0]),
                           ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(2)
    assert str(excinfo.value) == f'value 2 exceeds COMPU_VTAB ref range'


def test_compu_method_tab_verb_internal_to_physical_conversion_value_error():
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" TAB_VERB "" ""
        COMPU_TAB_REF ref
    /end COMPU_METHOD
    /begin COMPU_VTAB ref_ ""
         TAB_VERB
         1
         0 "A"
    /end COMPU_VTAB''')).encode())
    with pytest.raises(ValueError) as excinfo:
        CompuMethodTabVerb(Module(ast.PROJECT.MODULE[0]),
                           ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(0)
    assert str(excinfo.value) == f'COMPU_VTAB <ref> not found in MODULE <_>'


@pytest.mark.parametrize('a, b, c, d, e, f, internal_value, physical_value', [(0, 1, 0, 0, 0, 1, 0, 0),
                                                                              (0, 1, 0, 0, 0, 1, 1, 1),
                                                                              (0, 1, 0, 0, 0, 2, 1, 2),
                                                                              (1, 0, 0, 0, 0, 1, 4, -2)])
def test_compu_method_rat_func_internal_to_physical_conversion(a, b, c, d, e, f, internal_value, physical_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" RAT_FUNC "" ""
        COEFFS {a} {b} {c} {d} {e} {f}
    /end COMPU_METHOD''')).encode())
        assert CompuMethodRatFunc(Module(ast.PROJECT.MODULE[0]),
                                  ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(
            internal_value) == physical_value


@pytest.mark.parametrize('formula, internal_value, physical_value', [('X + 1', 1, 2),
                                                                     ('X1 + 1', 1, 2),
                                                                     ('X1 - 1', 1, 0),
                                                                     ('X1 * 2', 1, 2),
                                                                     ('X1 / 2', 2, 1),
                                                                     ('X1 ^ 2', 2, 4),
                                                                     ('X1 & 1', 3, 1),
                                                                     ('X1 | 1', 2, 3),
                                                                     ('X1 >> 1', 2, 1),
                                                                     ('X1 << 1', 1, 2),
                                                                     ('X1 XOR 1', 3, 2),
                                                                     ('~X1', 1, -2),
                                                                     ('sin(X1)', 0, 0),
                                                                     ('cos(X1)', 0, 1),
                                                                     ('tan(X1)', 0, 0),
                                                                     ('arcsin(X1)', 0, 0),
                                                                     ('arccos(X1)', 0, math.pi / 2),
                                                                     ('arctan(X1)', 0, 0),
                                                                     ('sinh(X1)', 0, 0),
                                                                     ('cosh(X1)', 0, 1),
                                                                     ('tanh(X1)', 0, 0),
                                                                     ('exp(X1)', 1, math.e),
                                                                     ('ln(X1)', math.e, 1),
                                                                     ('log(X1)', 10, 1),
                                                                     ('sqrt(X1)', 4, 2),
                                                                     ('abs(X1)', -1, 1),
                                                                     ('abs(X1) + 2 * X2', (-1, 2), 5)])
def test_compu_method_form_internal_to_physical_conversion(formula, internal_value, physical_value):
    with Parser() as p:
        ast = p.tree_from_a2l(project_string_minimal.format(module_string_minimal.format(f'''
    /begin COMPU_METHOD _ "" FORM "" ""
        /begin FORMULA
            "{formula}"
        /end FORMULA
    /end COMPU_METHOD''')).encode())
        assert CompuMethodForm(Module(ast.PROJECT.MODULE[0]),
                                  ast.PROJECT.MODULE[0].COMPU_METHOD[0]).convert_to_physical_from_internal(
            internal_value) == physical_value

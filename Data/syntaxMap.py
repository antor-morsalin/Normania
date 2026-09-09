SYNTAX_MAP = {

    # GENERAL VARIABLES

    "A": {
        "type": "general_variable",
        "syntax": "a",
        "group": "data",
        "value_type": "dynamic"
    },

    "B": {
        "type": "general_variable",
        "syntax": "b",
        "group": "data",
        "value_type": "dynamic"
    },

    "C": {
        "type": "general_variable",
        "syntax": "c",
        "group": "data",
        "value_type": "dynamic"
    },

    "X": {
        "type": "general_variable",
        "syntax": "x",
        "group": "data",
        "value_type": "dynamic"
    },

    "Y": {
        "type": "general_variable",
        "syntax": "y",
        "group": "data",
        "value_type": "dynamic"
    },

    "Z": {
        "type": "general_variable",
        "syntax": "z",
        "group": "data",
        "value_type": "dynamic"
    },


    # CONDITION VARIABLES
    "CONDITION1": {
        "type": "condition_variable",
        "syntax": "condition1",
        "group": "data",
        "value_type": "bool"
    },

    "CONDITION2": {
        "type": "condition_variable",
        "syntax": "condition2",
        "group": "data",
        "value_type": "bool"
    },


    # NUMBERS

    "0": {
        "type": "number_literal",
        "syntax": 0,
        "group": "data",
        "value_type": "number"
    },

    "1": {
        "type": "number_literal",
        "syntax": 1,
        "group": "data",
        "value_type": "number"
    },

    "2": {
        "type": "number_literal",
        "syntax": 2,
        "group": "data",
        "value_type": "number"
    },

    "3": {
        "type": "number_literal",
        "syntax": 3,
        "group": "data",
        "value_type": "number"
    },

    "4": {
        "type": "number_literal",
        "syntax": 4,
        "group": "data",
        "value_type": "number"
    },

    "5": {
        "type": "number_literal",
        "syntax": 5,
        "group": "data",
        "value_type": "number"
    },

    "6": {
        "type": "number_literal",
        "syntax": 6,
        "group": "data",
        "value_type": "number"
    },

    "7": {
        "type": "number_literal",
        "syntax": 7,
        "group": "data",
        "value_type": "number"
    },

    "8": {
        "type": "number_literal",
        "syntax": 8,
        "group": "data",
        "value_type": "number"
    },

    "9": {
        "type": "number_literal",
        "syntax": 9,
        "group": "data",
        "value_type": "number"
    },


    # STRINGS

    "HELLO": {
        "type": "string_literal",
        "syntax": "HELLO",
        "group": "data",
        "value_type": "string"
    },

    "GOOD MORNING": {
        "type": "string_literal",
        "syntax": "GOOD MORNING",
        "group": "data",
        "value_type": "string"
    },

    "RISE AND SHINE!": {
        "type": "string_literal",
        "syntax": "RISE AND SHINE!",
        "group": "data",
        "value_type": "string"
    },

    "NICE TO MEET YOU": {
        "type": "string_literal",
        "syntax": "NICE TO MEET YOU",
        "group": "data",
        "value_type": "string"
    },

    "GREAT JOB": {
        "type": "string_literal",
        "syntax": "GREAT JOB",
        "group": "data",
        "value_type": "string"
    },

    "KEEP TRYING": {
        "type": "string_literal",
        "syntax": "KEEP TRYING",
        "group": "data",
        "value_type": "string"
    },

    "YOU CAN DO IT": {
        "type": "string_literal",
        "syntax": "YOU CAN DO IT",
        "group": "data",
        "value_type": "string"
    },


    # CONTEXT-SENSITIVE TOKEN
    
    "IS": {
        "type": "context_sensitive",
        "syntax": {
            "assignment": "=",
            "comparison": "==",
        },
        "group": "assignment_comparison",
        "value_type": None
    },


    # ARITHMETIC OPERATORS

    "PLUS": {
        "type": "arithmetic_operator",
        "syntax": "+",
        "group": "arithmetic",
        "value_type": None
    },

    "MINUS": {
        "type": "arithmetic_operator",
        "syntax": "-",
        "group": "arithmetic",
        "value_type": None
    },

    "TIMES": {
        "type": "context_sensitive",
        "syntax": {
            "arithmetic": "*",
            "repeat": None
        },
        "group": "arithmetic_structure",
        "value_type": None
    },

    "DIVIDED BY": {
        "type": "arithmetic_operator",
        "syntax": "/",
        "group": "arithmetic",
        "value_type": None
    },


    # COMPARISON OPERATORS

    "IS NOT": {
        "type": "comparison_operator",
        "syntax": "!=",
        "group": "comparison",
        "value_type": None
    },

    "MORE THAN": {
        "type": "comparison_operator",
        "syntax": ">",
        "group": "comparison",
        "value_type": None
    },

    "LESS THAN": {
        "type": "comparison_operator",
        "syntax": "<",
        "group": "comparison",
        "value_type": None
    },

    "AT LEAST": {
        "type": "comparison_operator",
        "syntax": ">=",
        "group": "comparison",
        "value_type": None
    },

    "AT MOST": {
        "type": "comparison_operator",
        "syntax": "<=",
        "group": "comparison",
        "value_type": None
    },


    # BOOLEAN OPERATORS

    "AND": {
        "type": "boolean_operator",
        "syntax": "and",
        "group": "boolean",
        "value_type": None
    },

    "OR": {
        "type": "boolean_operator",
        "syntax": "or",
        "group": "boolean",
        "value_type": None
    },


    # =========================================================
    # OUTPUT
    # =========================================================
    "SHOW": {
        "type": "output_command",
        "syntax": "print",
        "group": "statement",
        "value_type": None
    },



    # PROGRAM STRUCTURE
 
    "IF": {
        "type": "condition_opener",
        "syntax": "if",
        "group": "structure",
        "value_type": None
    },

    "THEN": {
        "type": "if_delimiter",
        "syntax": None,
        "group": "auxiliary",
        "value_type": None
    },

    "REPEAT": {
        "type": "repeat_opener",
        "syntax": "for",
        "group": "structure",
        "value_type": None
    },

    "OTHERWISE": {
        "type": "alternative_branch",
        "syntax": "else",
        "group": "structure",
        "value_type": None
    },

    "END": {
        "type": "scope_closer",
        "syntax": None,
        "group": "auxiliary",
        "value_type": None
    }
}
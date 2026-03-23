# main 1
from ParserYal import YALexParser
from LexerGenerator import build_dfa_dict
from lexer_generator import generate_token_module, generate_lexer

parser = YALexParser().parse("minipython.yal")
dfa_dict = build_dfa_dict(parser.get_all_rules(), parser=parser)

generate_token_module(dfa_dict, "myToken.py")
generate_lexer(dfa_dict,output_path="thelexer.py")

from asyncio.windows_events import NULL
import logging
import re
from sly import Lexer, Parser
import yaml


logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s | %(levelname)s | %(message)s')
logging.disable()

tokens = {"literals": {}, "variables": {}, "tokens": {}}


# decorator for function logging
def logged(func):
    def wrapper(*args, **kwargs):
        try:
            logging.debug("Function '{0}', parameters : {1} and {2}".
                         format(func.__name__, args, kwargs))
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
    return wrapper


class Token:
    def __init__(self, token):
        self.token = token
        self.values = []

    def append(self, value):
        if isinstance(value, list):
            for v in value:
                v = str(v)
                if ".dat" not in v:
                    v = f"{v}.dat"
                self.values.append(v)
        else:
            v = str(value)
            if ".dat" not in v:
                v = f"{v}.dat"
            self.values.append(v)

    def remove(self, value):
        self.values.remove(value)

    def sort(self):
        self.values.sort()

    def __str__(self):
        return f"{self.token}: {', '.join(self.values)}"

    def regex_list(self):
        return f"({'|'.join(self.values)})"


@logged
def load_tokens(token_file):
    with open(token_file, 'r', encoding='UTF-8') as file:
        yaml_tokens = yaml.safe_load(file)
    for token_type in tokens:
        logging.info(f"Parsing tokens: {token_type}")
        for token in yaml_tokens[token_type]:
            t = Token(token)
            if isinstance(yaml_tokens[token_type], list):
                t.append(token)
            else:
                t.append(yaml_tokens[token_type][token])
            tokens[token_type][token] = t
        logging.debug(f"{len(tokens[token_type])} tokens added.")


class LDRLexer(Lexer):
    tokens = { ID, PRINT, PRINTLOC, ASSIGN, NUMBER, STRING, BLOCK }

    #Ignored characters between tokens (just whitespace for us)
    ignore = " \t"

    # Define a rule so we can track line numbers
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    # Rules for tokens are assigned dynamically in __init__()
    PRINT = "x"
    PRINTLOC = "x"
    ASSIGN = "x"
    ID = "x"

    @_(r"\d+")
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r'''("[^"\\]*(\\.[^"\\]*)*"|'[^'\\]*(\\.[^'\\]*)*')''')
    def STRING(self, t):
        t.value = self.remove_quotes(t.value)
        return t

    BLOCK = r"\w+.dat"

    def __init__(self):
        logging.info("Lexer created.")
        # Have to do a bit of extra work here since the sly package
        # really doesn't know how to deal with dynamic tokens. And we don't
        # know our tokens when the class is created.

        LDRLexer.PRINT = tokens["tokens"]["print"].regex_list()
        LDRLexer._attributes['PRINT'] = LDRLexer.PRINT

        LDRLexer.PRINTLOC = tokens["tokens"]["print_position"].regex_list()
        LDRLexer._attributes['PRINTLOC'] = LDRLexer.PRINTLOC

        LDRLexer.ASSIGN = tokens["tokens"]["assignment"].regex_list()
        LDRLexer._attributes['ASSIGN'] = LDRLexer.ASSIGN

        LDRLexer.ID = tokens["variables"]["ids"].regex_list()
        LDRLexer._attributes['ID'] = LDRLexer.ID

        LDRLexer._build()
        logging.debug("Lexer rules updated.")

    def remove_quotes(self, text: str):
        return text[1:-1] if text.startswith('\"') or text.startswith('\'') else text


class LDRParser(Parser):
    tokens = LDRLexer.tokens

    def __init__(self):
        self.names = {}
        self.errors = []
        self.print_line = 0
        self.header_printed = False

    def print_header(self):
        if self.header_printed:
            return
        print("0 L Lang output")
        print("0 Name: output.ldr")
        print("0 // This output was generated using the L language, using a")
        print("0 // LEGO CAD file (ldr file) input to compile into these results.")
        self.header_printed = True
        
    def wrapup(self):
        print("0 STEP")

    def lprint(self,  msg):
        for counter, c in enumerate(msg):
            self.lprint_pos(f"3005pt{c}.dat", 10 + 40 * counter, 0, 10 + -40 * self.print_line, 15)
        self.print_line += 1

    def lprint_pos(self, block, x, y, z, color=15):
        self.print_header()
        print(f"1 {color} {x} {y} {z} 1 0 0 0 1 0 0 0 1 {block}")
        

    @_('ID ASSIGN expr')
    def statement(self, p):
        logging.debug(f"ID ({p.ID}) ASSIGN expr ({p.expr})")
        self.names[p.ID] = p.expr

    @_('expr')
    def statement(self, p):
        logging.debug(f"expr ({p.expr})")
        return p.expr
    
    @_('NUMBER')
    def expr(self, p):
        return p.NUMBER

    @_('STRING')
    def expr(self, p):
        return p.STRING

    @_('ID')
    def expr(self, p):
        logging.debug(f"ID ({p.ID})")
        try:
            return self.names[p.ID]
        except LookupError:
            self.errors.append(('undefined', p.ID))
            return 0

    @_('PRINT statement')
    def statement(self, p):
        logging.debug(f"PRINT statement ({p.statement})")
        self.lprint(p.statement)

    def error(self, tok):
        self.errors.append(tok)


class LDRFile:
    def __init__(self, filename, args=''):
        logging.info(f"Creating LDR_File object for file: {filename}")
        self.filename = filename
        self.lines = []
        self.args = args.lower()

    @logged
    def lex(self):
        pre_parsed = self._pre_parse_lines()
        logging.info(f"Pre-parsing resulted in {len(pre_parsed)} lines of code")

        lexer = LDRLexer()
        logging.info("Beginning tokenizing...")

        # for tok in lexer.tokenize(pre_parsed):
        #     print(f"type={tok.type}, value={tok.value}")
        
        return lexer.tokenize(pre_parsed)


    @logged
    def parse(self):
        logging.info(f"Opening file: {self.filename}")
        with open(self.filename, 'r', encoding='UTF-8') as file:
            self.lines = file.readlines()
        logging.info(f"File read. {len(self.lines)} lines loaded.")
        logging.info("Adjusting tokens based on META TOKENS commands.")
        self._add_meta_tokens()
        
        pre_parsed = self._pre_parse_lines()
        logging.info(f"Pre-parsing resulted in {len(pre_parsed)} lines of code")
        lexer = LDRLexer()

        logging.info("Beginning tokenizing...")
        parser = LDRParser()
        # Add command line arguments:
        logging.info(f"Processing command line arguments: {self.args}")
        parser.names['3626ap01.dat'] = self.args

        for line in pre_parsed:
            parser.parse(lexer.tokenize(line))
        parser.wrapup()

    @logged
    def _pre_parse_lines(self):
        new_lines = []
        new_line = ""
        for one_line in self.lines:
            line = one_line.strip()
            logging.debug(f"Pre-parsing line: {line}")
            if line == "0 STEP":
                logging.debug(f"STEP line found. Full line: {new_line}")
                # 0 STEP lines function similarly to end of line markers
                # (or semicolons) in other languages.
                new_lines.append(new_line)
                new_line = ""
                continue
            if line[0] != "1":
                # Anything that isn't a block, we can ignore at this point.
                logging.debug("Non-block line found. Ignoring.")
                continue
            token = line.split(" ")[-1]
            logging.debug(f"Adding item: {token}")
            new_line = f"{new_line} {token}"

        if len(new_line) > 0:
            new_lines.append(new_line)

        result = "\n".join(new_lines)
        for key, value in tokens["literals"].items():
            rep = key
            rep = rep.split("_")[1] if "_" in rep else f"'{rep}'"
            for block in value.values:
                result = result.replace(block, rep)

        # Turn our separated characters ('a' 'b' ...) into a string ('ab...'):
        change = 0
        while change != len(result):
            change = len(result)
            result = re.sub(r"'([a-zA-Z]+)' '([a-zA-Z]+)'", r"'\1\2'", result)

        # Turn our separated numbers (1 2 ...) into a single number ('12...'):
        change = 0
        while change != len(result):
            change = len(result)
            result = re.sub(r" (\d+) (\d+) ", r"'\1\2'", result)

        return result.split("\n")

    @logged
    def _add_meta_tokens(self):
        logging.warning("***Adding meta tokens not implemented.")

from . import l_lang

import argparse
import logging


argparser = argparse.ArgumentParser()
argparser.add_argument("-t", "--tokens", type=str, default="tokens.yaml",
                    metavar="FILE", help="Token yaml file to define tokens")
argparser.add_argument("-l", "--logging", action="store_true",
                    help="Enable logging output (breaks ldr formatting for output)")
argparser.add_argument("--loglevel", type=int,
                    choices=[logging.CRITICAL, logging.ERROR,
                                logging.WARNING, logging.INFO, logging.DEBUG],
                    default=logging.WARNING,
                    help="Change log level")
argparser.add_argument("--arguments", type=str, default="",
                    help="Arguments to pass to the script")
argparser.add_argument("intput_file", type=str, help="ldr file to parse")
args = argparser.parse_args()

if args.logging:
    logging.disable(logging.NOTSET)
    logging.getLogger().setLevel(args.loglevel)
    logging.info(f"Enabling logging, level: {logging.getLevelName(args.loglevel)}")

l_lang.parser.load_tokens(args.tokens)

l_parser = l_lang.parser.LDRFile(args.intput_file, args.arguments)
l_parser.parse()

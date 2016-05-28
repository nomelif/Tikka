import parser
import codegen
import sys

if len(sys.argv) == 1:
    sys.stderr.write("No input files given.\n")
    sys.exit(1)
else:
    if sys.argv[1] == "--read-ast":
        sys.argv = sys.argv[1:]
        for fname in sys.argv[1:]:
            codegen.generate(parser.read(fname))
    else:
        for fname in sys.argv[1:]:
            codegen.generate(parser.parse(fname))

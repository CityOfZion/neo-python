import parser
import pprint


filepath = './boa/sources/Math.py'


st = parser.suite(open(filepath).read())
tu = st.totuple()

pprint.pprint(tu)
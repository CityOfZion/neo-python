import parser

import pprint

st = parser.suite(open('./boa/sources/Math.py').read())

tu = st.totuple()
pprint.pprint(tu)
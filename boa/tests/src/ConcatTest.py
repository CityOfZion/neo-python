from boa.code.builtins import concat

def Main():

    str1 = 'hello'
    str2 = 'world'

    str3 = concat(str1,str2)

    #this ends up being 'worldhello'
    #need to reverse the parameters...

    return str3
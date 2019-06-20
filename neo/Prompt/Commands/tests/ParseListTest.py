def main(cmd, args):
    print(args[0])
    if cmd == 1:
        return args[0] == 'aa'
    if cmd == 2:
        x = args[1]
        return x[0] == 'helloworld'
    if cmd == 3:
        lvl1 = args[1]
        lvl2 = lvl1[1]
        return lvl2[0] == 'helloworld'

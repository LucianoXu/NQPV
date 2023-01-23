import nqpv

code = '''
    def pf := proof [q] :
        { P1[q] };
        q *= X;
        { P0[q]}
    end
    show pf end
'''

fp = open("example.nqpv","w")
fp.write(code)
fp.close()

nqpv.entrance.verify("example.nqpv")
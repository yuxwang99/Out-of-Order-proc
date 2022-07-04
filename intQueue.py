
class IntQue:
    def __init__(self):
        self.intQueue = []
        self.issued_que = []
        self.ele = {}

        self.DestReg = 32
        self.OpAIsReady = True
        self.OpARegTag = 0
        self.OpAValue = 0
        self.OpBIsReady = True
        self.OpBRegTag = 0
        self.OpBValue = 0
        self.OpCode = "add"
        self.PC = 0

        self.ele["DestRegister"] = self.DestReg
        self.ele["OpAIsReady"] = self.OpAIsReady
        self.ele["OpARegTag"] = self.OpARegTag
        self.ele["OpAValue"] = self.OpAValue
        self.ele["OpBIsReady"] = self.OpBIsReady
        self.ele["OpBRegTag"] = self.OpBRegTag
        self.ele["OpBValue"] = self.OpBValue
        self.ele["OpCode"] = self.OpCode
        self.ele["PC"] = self.PC
        
    def empty(self):
        return len(self.intQueue)==0

    def len(self):
        return len(self.intQueue)

    def content(self):
        return self.intQueue

    def stepback(self,content):
        self.intQueue = content

    def add(self, 
            instructions: list, 
            regmaptable,
            logic_regs,
            busytable,
            RF,
            forwardingregs,
            DecodedPCs: list):
        #  Update Integer Queue
        # TODO: detect exception
        # num_ins = len(instructions)
        for (i,ins) in enumerate(instructions):
            IntQue_ele = {}
            op, dest, opA, opB = ins.split(' ')
            dest = int(dest[1:-1])
            opA = int(opA[1:-1])
            opB = int(opB)
            IntQue_ele["DestRegister"] = regmaptable[logic_regs[i]]
            opA_physical = regmaptable[opA]

            if(busytable[opA_physical]==False):
                IntQue_ele["OpAIsReady"] = True
                IntQue_ele["OpARegTag"] = 0
                IntQue_ele["OpAValue"] = RF[opA_physical]
            elif(opA_physical in forwardingregs):
                IntQue_ele["OpAIsReady"] = True
                IntQue_ele["OpARegTag"] = 0
                IntQue_ele["OpAValue"] = forwardingregs[opA_physical]
            else:
                IntQue_ele["OpAIsReady"] = False
                IntQue_ele["OpARegTag"] = opA_physical
                IntQue_ele["OpAValue"] = 0

            if(op=="addi"):
                IntQue_ele["OpBRegTag"] = 0
                IntQue_ele["OpBIsReady"] = True
                IntQue_ele["OpBValue"] = int(opB)

            else:
                opB = int(opB[1:len(opB)])
                opB_physical = regmaptable[opB]
                #TODO: 
                if(self.BusyTable[opB_physical]==False):
                    IntQue_ele["OpBIsReady"] = True
                    IntQue_ele["OpBRegTag"] = 0
                    IntQue_ele["OpBValue"] = RF[opB_physical]
                elif(opB_physical in forwardingregs):
                    IntQue_ele["OpBIsReady"] = True
                    IntQue_ele["OpBRegTag"] = 0
                    IntQue_ele["OpBValue"] = forwardingregs[opB_physical]
                else:
                    IntQue_ele["OpBIsReady"] = False
                    IntQue_ele["OpARegTag"] = opB_physical
                    IntQue_ele["OpBValue"] = 0
            IntQue_ele["OpCode"] = op
            IntQue_ele["PC"] = DecodedPCs[i]

            self.intQueue.append(IntQue_ele)
    
    def issue(self):
        issue_ins = 0
        
        for IntQue_ele in self.intQueue:
            issued_ins= {}
            if IntQue_ele["OpAIsReady"] and IntQue_ele["OpBIsReady"]:
                issue_ins += 1
                issued_ins["phy_des"] = IntQue_ele["DestRegister"]
                issued_ins["op"] = IntQue_ele["OpCode"]
                issued_ins["A"] = IntQue_ele["OpAValue"]
                issued_ins["B"] = IntQue_ele["OpBValue"]
                issued_ins["PC"] = IntQue_ele["PC"]
                self.issued_que.append(issued_ins)
                self.intQueue = self.intQueue[1:len(self.intQueue)]
            if issue_ins >= 4:
                break
        return self.issued_que



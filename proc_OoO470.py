import json
import numpy as np
import copy
from activeList import ActiveList
from intQueue import IntQue


class state_proc:
    def __init__(self):
        self.states = []
        self.state = {}
        self.PC = 0
        self.RF = np.zeros((64,),dtype='int')
        self.DIR = []
        self.exception = False
        self.ExceptionPC = 0
        self.RegMapTable = np.arange(32)
        self.FreeList = np.arange(32,64)
        self.BusyTable = np.array([False]*64)
        self.ActiveList = ActiveList()
        self.IntQue = IntQue()
        
        self.curBuffer = {}
        self.fetch_ins = []
        self.issued_que = []
        self.exec_ins = [None]*4
        self.availALU = [0]*4
        self.forwardingRegs = {}

    def activelist_empty(self):
        result = len(self.state["ActiveList"])==0
        return result and self.ActiveList.empty()

    def forwarding(self,key,val):
        self.forwardingRegs[key] = val

    def print_state(self):
        if self.exception:
            # step back
            self.PC = copy.copy(self.state["PC"])
            self.RF = copy.copy(self.state["PhysicalRegisterFile"])
            self.RegMapTable = self.state["RegisterMapTable"]
            self.FreeList = self.state["FreeList"]
            self.BusyTable = self.state["BusyBitTable"]
            self.ActiveList.stepback(self.state["ActiveList"])
            self.IntQue.stepback(self.state["IntegerQueue"])

            self.issued_que = self.curBuffer["issued_que"]
        else:
            # Only pass VALUE, NOT share address, update only if state is printed
            self.state["PC"] = copy.copy(self.PC)
            self.state["PhysicalRegisterFile"] = copy.copy(self.RF)
            self.state["DecodedPCs"] = copy.copy(self.DIR)
            self.state["ExceptionPC"] = copy.copy(self.ExceptionPC)
            self.state["Exception"] = copy.copy(self.exception)
            self.state["RegisterMapTable"] = copy.copy(self.RegMapTable)
            self.state["FreeList"] = copy.copy(self.FreeList)
            self.state["BusyBitTable"] = copy.copy(self.BusyTable)
            self.state["ActiveList"] = copy.copy(self.ActiveList.content())
            self.state["IntegerQueue"] = copy.copy(self.IntQue.content())

            self.curBuffer["issued_que"] = self.issued_que
        
        self.states.append(self.state)
        print(self.state)
        
    def update_state(self, instruct : list):

        self.fetch_decode(instruct)
        self.rename_dispatch()
        self.issue()
        self.exec()
        self.commit()
    
    def excep_handler(self):
        return
        
    def fetch_decode(self, instruct : list):

        for ins in instruct:
            self.fetch_ins.append(ins)
            if self.exception:
                self.PC = "0x10000"
                # Exception
                # ???
            else:
                self.DIR.append(str(self.PC))
                self.PC += 1

    def rename_dispatch(self):
        resource_avail = self.ActiveList.len()<32 and \
                        self.ActiveList.len()<32 
        if (resource_avail and len(self.state["DecodedPCs"])>0):
            if len(self.state["DecodedPCs"])<4:
                num_DecPC = len(self.state["DecodedPCs"])
            else:
                num_DecPC = 4
            # Update the ActiveList and get the updated content
            add_content = self.ActiveList.add(self.fetch_ins[0:num_DecPC],
                                        self.state["RegisterMapTable"],
                                        self.state["DecodedPCs"])
            logic_regs = add_content[2]
            
            for logic_reg in logic_regs:
                self.RegMapTable[logic_reg] = self.FreeList[0] #rename the register
                self.BusyTable[self.FreeList[0]] = True # Change the status of the logical register in busy table
                self.FreeList = self.FreeList[1:len(self.FreeList)] # Remove it from freelist
            
            # Update Integer Queue
            self.IntQue.add(self.fetch_ins[0:num_DecPC],
                        self.RegMapTable,
                        logic_regs,
                        self.BusyTable,
                        self.RF,
                        self.forwardingRegs,
                        self.state["DecodedPCs"])


            self.fetch_ins = self.fetch_ins[num_DecPC:len(self.fetch_ins)]
            self.DIR = self.DIR[num_DecPC:len(self.DIR)]
            
    def issue(self):
        if len(self.state["IntegerQueue"]):
            self.issued_que = self.IntQue.issue() 
        # return issued instruction que

    def exec(self):
        
        i = 0
        for (i,ins) in enumerate(self.curBuffer["issued_que"]):
        
            if(self.availALU[i]==0):
                # ALU available, start new computation
                self.exec_ins[i] = ins
                
                self.availALU[i] += 1
            elif(self.availALU[i]==1):
                # mark active list done: True
                if(self.exec_ins[i]["op"]=="add" or self.exec_ins[i]["op"]=="addi"):
                    self.exec_ins[i]["result"] = self.exec_ins[i]["A"]+self.exec_ins[i]["B"]
                elif(self.exec_ins[i]["op"]=="sub"):
                    self.exec_ins[i]["result"] = self.exec_ins[i]["A"]-self.exec_ins[i]["B"]
                elif(self.exec_ins[i]["op"]=="mulu"):
                    self.exec_ins[i]["result"] = self.exec_ins[i]["A"]*self.exec_ins[i]["B"]
                elif(self.exec_ins[i]["op"]=="divu"):
                    if self.exec_ins[i]["B"]==0:
                        self.exception = True
                        return
                    self.exec_ins[i]["result"] = self.exec_ins[i]["A"]/self.exec_ins[i]["B"]
                elif(self.exec_ins[i]["op"]=="remu"):
                    if self.exec_ins[i]["B"]==0:
                        self.exception = True
                        
                        return
                    self.exec_ins[i]["result"] = self.exec_ins[i]["A"]%self.exec_ins[i]["B"]
                    
                self.availALU[i] = 0 #computation finished, available
                self.issued_que = self.issued_que[1:len(self.issued_que)] #remove instructions saved in issue register
                self.forwarding(self.exec_ins[i]["phy_des"],self.exec_ins[i]["result"])

            if i>=3:
                break
        
                
    def commit(self):
        if self.exception:
            # TODO : exception handler
            self.ExceptionPC = self.PC
            
        else:
            # update free_list, self.BusyTable, self.RF, self.forwardingRegs
            self.FreeList, self.BusyTable, self.RF,self.forwardingRegs = self.ActiveList.commit(self.exec_ins,
                                                                            self.FreeList,
                                                                            self.BusyTable,
                                                                            self.RF,
                                                                            self.forwardingRegs,
                                                                            self.RegMapTable)

instruction = [
"addi x1, x0, 1",
"addi x2, x0, 2",
"addi x3, x0, 10",
"addi x4, x0, 20"
]

proc = state_proc()
noinstruction = len(instruction)==0
clk = 0
active_list_empty = True
while(not noinstruction or not active_list_empty):
    print("====="+str(clk)+"====")
    proc.print_state()
    proc.update_state(instruction)
    noinstruction = len(instruction)==0
    instruction = instruction[4:len(instruction)]
    
    active_list_empty = proc.activelist_empty()
    clk += 1

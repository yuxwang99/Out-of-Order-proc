import numpy as np
class ActiveList:
    def __init__(self):
        self.ActiveList = []
        self.activeIns = {}
        self.Done = "false"
        self.Exception = "false"
        self.LogicalDestination = 0
        self.OldDestination = 0
        self.PC = 0
        
        self.activeIns["Done"] = self.Done
        self.activeIns["Exception"] = self.Exception
        self.activeIns["LogicalDestination"] = self.LogicalDestination
        self.activeIns["OldDestination"] = self.OldDestination
        self.activeIns["PC"] = self.PC
        
    def empty(self):
        return len(self.ActiveList)==0

    def len(self):
        return len(self.ActiveList)

    def content(self):
        return self.ActiveList

    def stepback(self,content):
        self.ActiveList = content

    def add(self, 
            instructions: list, 
            regmaptable,
            DecodedPCs: list):
        num_ins = len(instructions)
         # States in ActiveList
        Done, excep, logic_dest,old_dest, PC = self.create(instructions,regmaptable,DecodedPCs)
        # States in Integer Queue
        for i in range(num_ins):
            Activelist_ele = {}
            Activelist_ele["Done"] = Done[i]
            Activelist_ele["Exception"] = excep[i]
            Activelist_ele["LogicalDestination"] = logic_dest[i]
            Activelist_ele["OldDestination"] = old_dest[i]
            Activelist_ele["PC"] = PC[i]
            self.ActiveList.append(Activelist_ele)
        return Done,excep,logic_dest,old_dest,PC

    def create(self, 
            instructions: list, 
            regmaptable,
            DecodedPCs: list):
        num_ins = len(instructions)
         # States in ActiveList
        Done = [False]*num_ins
        excep = [False]*num_ins
        logic_regs = []
        old_regs = []
        PCs = []
        # States in Integer Queue
        for (idx,ins) in enumerate(instructions,1):
            # Update active list
            op, dest, opA, opB = ins.split(' ')
            dest = int(dest[1:-1])
            opA = int(opA[1:-1])
            opB = int(opB)
            logic_regs.append(dest)
            old_regs.append(regmaptable[dest])
            PCs.append(DecodedPCs[idx-1])
        return Done,excep,logic_regs,old_regs,PCs
    
    def change_state(self, PC, key:str, value):
        for Activelist_ele in self.ActiveList:
            if Activelist_ele["PC"] == PC:
                Activelist_ele[key] = value
                break
        return self.ActiveList

    def retire(self):
        # Instruction should retire in order
        for active_ele in self.ActiveList:
            if active_ele["Done"]==True:
                self.ActiveList = self.ActiveList[1:len(self.ActiveList)]
                
            else:
                break

    def commit(self,comp_result,free_list,busytable,regFile,forwardingregs, maptable):
        self.retire()
        for (i,active_ele) in enumerate(self.ActiveList):
            key_PC = active_ele["PC"]
            # search result for PC
            for proc_result in comp_result:
                if proc_result==None:
                    continue
                if proc_result["PC"]==key_PC:
                    try:
                        if proc_result["result"]:
                            active_ele["Done"] = True
                            freeid = maptable[active_ele["LogicalDestination"]]
                            busytable[freeid] = False
                            regFile[freeid] = proc_result["result"]
                        
                            if freeid in forwardingregs:
                                del forwardingregs[freeid]
                            free_list = np.append(free_list,active_ele["OldDestination"])
                            break
                    except:
                        return free_list,busytable,regFile,forwardingregs
            if i>=3:
                break
        return free_list,busytable,regFile,forwardingregs

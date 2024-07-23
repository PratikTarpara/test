"""
Copyright (c) 2023 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author:  
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
"""

try:
    from utils.sip import Actor,AState
except ImportError:
    from src.main.utils.sip import Actor,AState

class WaitforNewOrder(AState):
    message_in =  ["Order",]       
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.SendCFP_Enabled = True
            
    
    def actions(self) -> None:
        if (self.wait_untill_message(1, WaitforNewOrder.message_in)):
            message = self.receive(WaitforNewOrder.message_in[0])
            self.save_in_message(message)
            self.push("Order",message)
            submodel_sr = message["interactionElements"]
            self.push("submodel",submodel_sr)
            print("Order received")
        
    def transitions(self) -> object:
        if (self.SendCFP_Enabled):
            return "SendCFP"
               
class SendCFP(AState):
    message_out =  ["callForProposal",]
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitForSPProposal_Enabled = True
            
    def create_outbound_message(self,msg_type) -> list:
        message = self.retrieve("Order")
        receiverId ="ww.ovgu.de/aas/62070ae3-88c7-4820-bca0-8dbd1516fbd3"
        receiverRole = "ServiceProvider"
        conV1 = message["frame"]["conversationId"]
        oMessage_Out = self.create_i40_message(msg_type,conV1,receiverId,receiverRole)
        submodel = self.retrieve("submodel")
        oMessage_Out["interactionElements"].append(submodel)
        self.save_out_message(oMessage_Out)
        return [oMessage_Out]
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        self.send(self.create_outbound_message(SendCFP.message_out[0]))
        if (self.WaitForSPProposal_Enabled):
            return "WaitForSPProposal"

class WaitForSPProposal(AState):
    message_in =  ["OrderRefused", "Proposal", ]       
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforNewOrder_Enabled = True
        self.WaitForUserConfirmation_Enabled = True
            
    
    def actions(self) -> None:
        if (self.wait_untill_message(1, WaitForSPProposal.message_in)):
            print("Service provider proposal received.")
            Orderrefuse = self.receive(WaitForSPProposal.message_in[0])
            Proposal = self.receive(WaitForSPProposal.message_in[1])
            if Proposal:
                self.WaitforNewOrder_Enabled = False
            if Orderrefuse:
                self.WaitForUserConfirmation_Enabled = False
            #if Proposal["frame"]["type"] == "Proposal":
            #    self.WaitforNewOrder_Enabled = False
            #if Orderrefuse["frame"]["type"] == "OrderRefused":
            #    self.WaitForUserConfirmation_Enabled = False
                print("Order reject due to data mismatched.") 
        
    def transitions(self) -> object:
        if (self.WaitforNewOrder_Enabled):
            return "WaitforNewOrder"
        if (self.WaitForUserConfirmation_Enabled):
            return "WaitForUserConfirmation"

class WaitForUserConfirmation(AState):
    message_in =  ["Confirm", "Cancel",]       
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.RejectProposal_Enabled = True
        self.AcceptProposal_Enabled = True
            
    
    def actions(self) -> None:
        if (self.wait_untill_message(1, WaitForUserConfirmation.message_in)):
            message2 = (self.receive(WaitForUserConfirmation.message_in[0])) or (self.receive(WaitForUserConfirmation.message_in[1]))
            self.save_in_message(message2)
            self.push("Decesion",message2)
            Received_Mesasage_2 = message2["frame"]["type"]
            if Received_Mesasage_2 == "Confirm":
                self.RejectProposal_Enabled = False
            elif Received_Mesasage_2 == "Cancel":
                self.AcceptProposal_Enabled = False
                print("Customer refused the proposal.") 
        
    def transitions(self) -> object:
        if (self.RejectProposal_Enabled):
            return "RejectProposal"
        if (self.AcceptProposal_Enabled):
            return "AcceptProposal"

class AcceptProposal(AState):
    message_out =  ["Accept",]
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforNewOrder_Enabled = True
            
    def create_outbound_message(self,msg_type) -> list:
        message = self.retrieve("Order")
        receiverId ="ww.ovgu.de/aas/62070ae3-88c7-4820-bca0-8dbd1516fbd3"
        receiverRole = "ServiceProvider"
        conV1 = message["frame"]["conversationId"]
        oMessage_Out = self.create_i40_message(msg_type,conV1,receiverId,receiverRole)
        #submodel = self.GetSubmodelById('submodelId')
        #oMessage_Out["interactionElements"].append(submodel)
        self.save_out_message(oMessage_Out)
        return [oMessage_Out]
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        self.send(self.create_outbound_message(AcceptProposal.message_out[0]))
        if (self.WaitforNewOrder_Enabled):
            return "WaitforNewOrder"
        
class RejectProposal(AState):
    message_out =  ["Reject",]
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforNewOrder_Enabled = True
            
    def create_outbound_message(self,msg_type) -> list:
        message = self.retrieve("Order")
        receiverId ="ww.ovgu.de/aas/62070ae3-88c7-4820-bca0-8dbd1516fbd3"
        receiverRole = "ServiceProvider"
        conV1 = message["frame"]["conversationId"]
        oMessage_Out = self.create_i40_message(msg_type,conV1,receiverId,receiverRole)
        #submodel = self.GetSubmodelById('submodelId')
        #oMessage_Out["interactionElements"].append(submodel)
        self.save_out_message(oMessage_Out)
        return [oMessage_Out]
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        self.send(self.create_outbound_message(RejectProposal.message_out[0]))
        if (self.WaitforNewOrder_Enabled):
            return "WaitforNewOrder"
           

class ServiceRequester(Actor):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''      
        Actor.__init__(self,"ServiceRequester",
                       "www.admin-shell.io/interaction/bidding",
                       "Service Requisition","WaitforNewOrder")
                        

    def start(self):
        self.run("WaitforNewOrder")


if __name__ == '__main__':
    
    lm2 = ServiceRequester()
    lm2.Start('msgHandler')

"""
Copyright (c) 2023 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: 
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
"""
import subprocess
import os
import sys

try:
    from Slicer.slicer_utils import convert_stl_to_gcode, extract_gcode_info
except ImportError:
    from src.main.Slicer.slicer_utils import convert_stl_to_gcode, extract_gcode_info
    
try:
    from utils.sip import Actor,AState
except ImportError:
    from src.main.utils.sip import Actor,AState

class WaitforcallForProposal(AState):
    message_in =  ["callForProposal",]       
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.AcceptOrder_Enabled = True
        self.RejectOrder_Enabled = True
            
    
    def actions(self) -> None:
        if (self.wait_untill_message(1, WaitforcallForProposal.message_in)):
            print("callForProposal received")
            message = self.receive(WaitforcallForProposal.message_in[0])
            self.save_in_message(message)
            self.push("callForProposal",message)
            submodel_sr = message["interactionElements"][0][0]
            SR_Dim= submodel_sr['submodelElements'][0]['value']
            SR_Layer_Height = submodel_sr['submodelElements'][1]['value'][0]['value']
            submodel_sp = self.GetSubmodelById("ww.ovgu.de/submodel/SP_Test")
            SP_Dim= submodel_sp['submodelElements'][0]['value']
            SP_Layer_Heights = []
            for element in submodel_sp["submodelElements"]:
                if element["idShort"] == "SP_Layer_Height":
                    for item in element["value"]:
                        SP_Layer_Heights.append(str(item["value"]))
        
            if((SR_Dim > SP_Dim) or (SR_Layer_Height not in SP_Layer_Heights)):
                self.AcceptOrder_Enabled = False  
            else:
                self.RefuseOrder_Enabled = False
            
            if (SR_Dim <= SP_Dim):
                print("Dimension is matched")
            if (SR_Layer_Height in SP_Layer_Heights):
                print("Layer height matched")
        
    def transitions(self) -> object:
        if (self.AcceptOrder_Enabled):
            return "AcceptOrder"
        if (self.RejectOrder_Enabled):
            return "RejectOrder"

class RejectOrder(AState):
    message_out =  ["OrderRefused",]
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforcallForProposal_Enabled = True
            
    def create_outbound_message(self,msg_type) -> list:
        message = self.retrieve("callForProposal")
        receiverId ="ww.ovgu.de/aas/62070ae3-88c7-4820-bca0-8dbd1516fbd3"
        receiverRole = "ServiceRequester"
        conV1 = message["frame"]["conversationId"]
        oMessage_Out = self.create_i40_message(msg_type,conV1,receiverId,receiverRole)
        #submodel = self.GetSubmodelById('submodelId')
        #oMessage_Out["interactionElements"].append(submodel)
        self.save_out_message(oMessage_Out)
        return [oMessage_Out]  
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        self.send(self.create_outbound_message(RejectOrder.message_out[0]))
        if (self.WaitforcallForProposal_Enabled):
            return "WaitforcallForProposal"
   
class AcceptOrder(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.SliceFile_Enabled = True
            
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        if (self.SliceFile_Enabled):
            return "SliceFile"   

class SliceFile(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.ExtractInformation_Enabled = True
            
    
    def actions(self) -> None:
        # Paths and layer height
        #use relative path
        # Paths and parameters
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Script directory: {script_dir}")

        # Correct the path to the STL file
        stl_file_path = os.path.normpath(os.path.join(script_dir, '../slicer/test.stl'))
        output_folder = os.path.normpath(os.path.join(script_dir, '../slicer/output'))
        message = self.retrieve("callForProposal")
        self.save_in_message(message)
        submodel_sr = message["interactionElements"][0][0]
        SR_Layer_Height = submodel_sr['submodelElements'][1]['value'][0]['value']
        manual_layer_height = SR_Layer_Height

        # Convert STL to G-code
        output_gcode_file = convert_stl_to_gcode(stl_file_path, output_folder, manual_layer_height)
        self.push("Gcode", output_gcode_file)
        if output_gcode_file:
            print("STL to G-code converted.")
        else:
            print("STL to G-code conversion failed.") 
        
    def transitions(self) -> object:
        if (self.ExtractInformation_Enabled):
            return "ExtractInformation"

class ExtractInformation(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.PriceCalculation_Enabled = True
            
    
    def actions(self) -> None:
        Gcode_Info = self.retrieve("Gcode")
        Gcode_Parameter=extract_gcode_info(Gcode_Info)
        self.push("filament_used",Gcode_Parameter['filament_used'])
        self.push("estimated_print_time",Gcode_Parameter['estimated_print_time'])
        self.push("Material_Type",Gcode_Parameter['material_type'])
                
        print("filament_used(cm3):",Gcode_Parameter['filament_used'])
        print("estimated_print_time:",Gcode_Parameter['estimated_print_time'])
        print("Material_Type:",Gcode_Parameter['material_type'])
        
    def transitions(self) -> object:
        if (self.PriceCalculation_Enabled):
            return "PriceCalculation"

class PriceCalculation(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.SendProposal_Enabled = True
            
    
    def actions(self) -> None:
        # Material Cost       
        Material_Volume_cm3 = self.retrieve("filament_used")
        Material = self.retrieve("Material_Type")
        if Material == 'PLA':
            Material_Density_g_cm3 = 1.25
            # Calculate the mass of the printed material in kg
        material_mass_kg = Material_Volume_cm3 * Material_Density_g_cm3 / 1000  # converting g to kg   
        material_cost_per_kg = 3 
        material_cost = material_mass_kg * material_cost_per_kg
        
        # Electricity cost        
        seconds = 0
        minutes = 0
        hours = 0
        days = 0
        Print_Time = self.retrieve("estimated_print_time")
            # Split the time string into parts
        time_parts = Print_Time.split()
        for part in time_parts:
            if part.endswith('s'):
                seconds = int(part[:-1])
            elif part.endswith('m'):
                minutes = int(part[:-1])
            elif part.endswith('h'):
                hours = int(part[:-1]) 
            elif part.endswith('d'):
                days = int(part[:-1])           
            # Convert total time to hours
        printing_time_hours = (seconds / 3600) + (minutes / 60) + (hours) + (days * 24) 

        printer_power_kw = 0.9
        electricity_cost_per_kwh = 0.4
        electricity_cost = printer_power_kw * printing_time_hours * electricity_cost_per_kwh
        
        # Worker cost
        working_time_hours = 0.2
        wages_per_hour = 13
        worker_cost = working_time_hours * wages_per_hour

        # Calculate the total cost before profit
        total_cost_before_profit = material_cost + electricity_cost + worker_cost
    
        # Calculate profit
        profit_percentage = 25
        profit = total_cost_before_profit * (profit_percentage / 100)
    
        # Calculate the total cost
        total_cost = total_cost_before_profit + profit
        self.push("Total_Cost",total_cost)
        print("Total cost for printing:", total_cost)
        
    def transitions(self) -> object:
        if (self.SendProposal_Enabled):
            return "SendProposal"
 
class SendProposal(AState):
    message_out =  ["Proposal",]
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitForApproval_Enabled = True
            
    def create_outbound_message(self,msg_type) -> list:
        message = self.retrieve("callForProposal")
        receiverId ="ww.ovgu.de/aas/62070ae3-88c7-4820-bca0-8dbd1516fbd3"
        receiverRole = "ServiceRequester"
        conV1 = message["frame"]["conversationId"]
        oMessage_Out = self.create_i40_message(msg_type,conV1,receiverId,receiverRole)
        Print_Time = self.retrieve("estimated_print_time")
        Total_Cost = self.retrieve("Total_Cost")
        #submodel = self.GetSubmodelById('submodelId')        
        oMessage_Out["interactionElements"].append([f"Estimated time: {Print_Time}", f"Cost: {Total_Cost:.2f} Euros"])
        self.save_out_message(oMessage_Out)
        return [oMessage_Out] 
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        self.send(self.create_outbound_message(SendProposal.message_out[0]))
        if (self.WaitForApproval_Enabled):
            return "WaitForApproval"

class WaitForApproval(AState):
    message_in =  ["Accept", "Reject",]       
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.AcceptApproval_Enabled = True
        self.RejectApproval_Enabled = True
            
    
    def actions(self) -> None:
        print("customer decesion.")
        if (self.wait_untill_message(1, WaitForApproval.message_in)):
            print("customer decesion received.")
            Accept = self.receive_all(WaitForApproval.message_in[0])
            Reject = self.receive_all(WaitForApproval.message_in[1])
            if Accept:
                self.RejectApproval_Enabled = False
            if Reject:
                self.AcceptApproval_Enabled = False
        
    def transitions(self) -> object:
        if (self.AcceptApproval_Enabled):
            return "AcceptApproval"
        if (self.RejectApproval_Enabled):
            return "RejectApproval"
   
class AcceptApproval(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforcallForProposal_Enabled = True
            
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        if (self.WaitforcallForProposal_Enabled):
            return "WaitforcallForProposal"
                                                
class RejectApproval(AState):
    
    def initialize(self):
        # Gaurd variables for enabling the transitions
        self.WaitforcallForProposal_Enabled = True
            
    
    def actions(self) -> None:
        pass
        
    def transitions(self) -> object:
        if (self.WaitforcallForProposal_Enabled):
            return "WaitforcallForProposal"
            

class ServiceProvider(Actor):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''      
        Actor.__init__(self,"ServiceProvider",
                       "www.admin-shell.io/interaction/bidding",
                       "Service Provision","WaitforcallForProposal")
                        

    def start(self):
        self.run("WaitforcallForProposal")


if __name__ == '__main__':
    
    lm2 = ServiceProvider()
    lm2.Start('msgHandler')

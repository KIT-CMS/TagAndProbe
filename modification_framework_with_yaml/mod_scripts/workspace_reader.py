import ROOT 


func_dictionary = {


# "ID_pt_bins_inc_eta" : ["m_id_ic_embed", "m_id_ic_mc"],  # just assign the value with eta=2.4
"ID_pt_eta_bins" : ["m_id_ic_embed_ratio","m_id_ic_ratio",  ],

# "Iso_pt_bins_inc_eta" : ["m_iso_ic_embed","m_iso_ic_mc",  ], # just assign the value with eta=2.4
"Iso_pt_eta_bins" : ["m_iso_ic_embed_ratio", "m_iso_ic_ratio"],

# "AIso1_pt_bins_inc_eta" : ["m_iso_ic_embed", "m_iso_ic_mc"],  #we don't need antiisolation so much 
# "AIso1_pt_eta_bins" : ["m_iso_ic_embed", "m_iso_ic_mc"],  #we don't need antiisolation so much

# "AIso2_pt_bins_inc_eta" : ["m_iso_ic_embed", "m_iso_ic_mc"],  #we don't need antiisolation so much 
# "AIso2_pt_eta_bins" : ["m_iso_ic_embed", "m_iso_ic_mc"],  #we don't need antiisolation so much

"Trg_pt_eta_bins" : ["m_trg_ic_embed_ratio", "m_trg_ic_ratio"],

# "Trg_AIso1_pt_bins_inc_eta" : ["m_trg_ic_embed", "m_trg_ic_mc"], # we don't care about antiisolation
 
# "Trg_AIso2_pt_bins_inc_eta" : ["m_trg_ic_embed", "m_trg_ic_mc"], # we don't care about antiisolation



}


class WorkspaceReader:

    def __init__(self, file):

        ws_file = ROOT.TFile(file, "read")
        self.ws = ws_file.Get("w")


        
    def get_sfs_2D(self, pt, eta, name, emb_mc_flag):
        if name in func_dictionary.keys():

            result = 1.0

            if pt > 200.0:
                return result

            if pt < 200.0:

                if emb_mc_flag == "emb":

                    hist = self.ws.obj("hist_"+func_dictionary[name][0])

                elif emb_mc_flag == "mc":
                    hist = self.ws.obj("hist_"+func_dictionary[name][1])

                result = hist.GetBinContent( hist.GetXaxis().FindBin(pt) , hist.GetYaxis().FindBin(eta) )
        
            return result

            
        elif name not in func_dictionary.keys():
            return 1.0



    def get_emb_sel_sfs(self, pt_1, eta_1, pt_2, eta_binning):
        sfs = []

        for eta_2 in eta_binning[:-1]:
            argset = self.ws.argSet("gt1_pt,gt1_eta,gt2_pt,gt2_eta")

            argset.setRealValue("gt1_pt", pt_1 )
            argset.setRealValue("gt1_eta", eta_1)


            argset.setRealValue("gt2_pt", pt_2)
            argset.setRealValue("gt2_eta", eta_2)

            roofunction = self.ws.function("m_sel_trg_ic_data")

            efficiency = roofunction.getVal(argset)
            efficiency = min(1./efficiency, 20) 

            sfs.append(efficiency)

        return sfs
    

    def get_emb_id_sel(self, pt,  eta_binning):
        sfs = []

        for eta in eta_binning[:-1]:
            argset = self.ws.argSet("gt_pt,gt_eta")

            argset.setRealValue("gt_pt", pt )
            argset.setRealValue("gt_eta", eta)

            roofunction = self.ws.function("m_sel_id_ic_data")

            efficiency = roofunction.getVal(argset)
            efficiency = min(1./efficiency, 20) 

            sfs.append(efficiency)

        return sfs







            
    
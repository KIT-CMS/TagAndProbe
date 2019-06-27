#!/bin/env python
import subprocess
import fitTagAndProbe_script
import plotEffSlices_script
import argparse
#from joblib import Parallel, delayed

parser = argparse.ArgumentParser()

parser.add_argument(
    '--channel', default="m", required=True)
parser.add_argument(
    '--fit', action="store_true")
parser.add_argument(
    '--plot', action="store_true")
parser.add_argument(
    "--cores", default=10
)
args = parser.parse_args()
if "sm" in args.channel:
    dir = "output_17_5/tag_and_probe_sm_v17_4/"
elif "dm" in args.channel:
    dir = "output_17_5/tag_and_probe_dm_v17_4/"
elif "e" in args.channel:
    dir = "output_17_5/tag_and_probe_e_v17_4/"
else:
    "Only Options are sm / dm / e !!"
num_cores = args.cores
parameters = {
    "Trg_AIso1_pt_bins_inc_eta": {
        "SMALL": "Trg_AIso1inc",
        "DIR": dir,
        "TITLE": "Trg_AIso1_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_AIso1_pt_eta_bins": {
        "SMALL": "eff.Trg_AIso1",
        "DIR": dir,
        "TITLE": "Trg_AIso1_pt_eta_bins",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_AIso2",
        "DIR": dir,
        "TITLE": "Trg_AIso2_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_AIso2_pt_eta_bins": {
        "SMALL": "eff.Trg_AIso2",
        "DIR": dir,
        "TITLE": "Trg_AIso2_pt_eta_bins",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "ID_pt_eta_bins": {
        "SMALL": "eff.ID",
        "DIR": dir,
        "TITLE": "CMSSHAPE",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Iso_pt_eta_bins": {
        "SMALL": "eff.Iso",
        "DIR": dir,
        "TITLE": "Iso_{rel} < 0.15",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "AIso1_pt_eta_bins": {
        "SMALL": "eff.AIso1",
        "DIR": dir,
        "TITLE": "AIso1_pt_eta_bins",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "AIso2_pt_eta_bins": {
        "SMALL": "eff.AIso2",
        "DIR": dir,
        "TITLE": "AIso2_pt_eta_bins",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu24_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu24",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu24_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg24_AIso1",
        "DIR": dir,
        "TITLE": "Trg24_AIso1_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu24_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg24_AIso2",
        "DIR": dir,
        "TITLE": "Trg24_AIso2_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_AIso1",
        "DIR": dir,
        "TITLE": "Trg27_AIso1_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_AIso2",
        "DIR": dir,
        "TITLE": "Trg27_AIso2_pt_bins_inc_eta",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_or_IsoMu24_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu24 or IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_or_IsoMu24_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_AIso1",
        "DIR": dir,
        "TITLE": "Trg IsoMu24 or IsoMu27 AIso1",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_IsoMu27_or_IsoMu24_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg24_27_AIso2",
        "DIR": dir,
        "TITLE": "Trg IsoMu24 or IsoMu27 AIso2",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    #     "LooseIso_pt_eta_bins": {
    #     "SMALL": "eff.Iso",
    #     "DIR": dir,
    #     "TITLE": "Iso_{rel} < 0.2",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
}
el_parameters = {
    "ID80_pt_eta_bins": {
        "SMALL": "eff.ID",
        "DIR": dir,
        "TITLE": "Non-trig MVA ID 17 - WP80",
        "BKG": "CMSShape",
        "SIG": "DoubleVCorr"
    },
    "ID90_pt_eta_bins": {
        "SMALL": "eff.ID",
        "DIR": dir,
        "TITLE": "Non-trig MVA ID 17 - WP90",
        "BKG": "CMSShape",
        "SIG": "DoubleVCorr"
     },
    "Iso_pt_eta_bins": {
        "SMALL": "eff.Iso",
        "DIR": dir,
        "TITLE": "Iso_{rel} < 0.15",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "AIso_pt_eta_bins": {
        "SMALL": "eff.Iso",
        "DIR": dir,
        "TITLE": "Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(27 || 32|| 32fb || 35)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_AIso1inc",
        "DIR": dir,
        "TITLE": "Trg Ele(27 || 32|| 32fb || 35)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_Iso_pt_eta_bins":{
        "SMALL": "eff.Trg_27Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(27)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(27)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_Iso_pt_eta_bins":{
        "SMALL": "eff.Trg_32Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(32)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg32_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(32)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_fb_Iso_pt_eta_bins":{
        "SMALL": "eff.Trg_32_fbIso",
        "DIR": dir,
        "TITLE": "Trg Ele(32_fb)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_fb_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg32_fb_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(32_fb)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg35_Iso_pt_eta_bins":{
        "SMALL": "eff.Trg_35Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(35)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg35_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg35_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(35)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg32_Iso_pt_eta_bins":{
        "SMALL": "eff.Trg_27_or_32Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 32)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg32_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_or_32AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 32)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg35_Iso_pt_eta_bins" :{
        "SMALL": "eff.Trg_27_or_35_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 35)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg35_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_or_35_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 35)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_or_Trg35_Iso_pt_eta_bins" :{
        "SMALL": "eff.Trg_32_or_35_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(32 or 35)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg32_or_Trg35_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg32_or_35_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(32 or 35)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg32_or_Trg35_Iso_pt_eta_bins" :{
        "SMALL": "eff.Trg_27_or_32_or_35_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 32 or 35)",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    "Trg27_or_Trg32_or_Trg35_AIso_pt_bins_inc_eta": {
        "SMALL": "eff.Trg27_or_32_or_35_AIsoinc",
        "DIR": dir,
        "TITLE": "Trg Ele(27 or 32 or 35)| Iso_{rel} #in [0.15,0.5]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr"
    },
    #     "Trg27_or_Trg32_or_Trg32fb_Iso_pt_eta_bins":{
    #     "SMALL": "eff.Trg_27_or_32_or_32fbIso",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32fb)",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "Trg27_or_Trg32_or_Trg32fb_AIso_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg27_or_32_or_32fb_AIsoinc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32fb)| Iso_{rel} #in [0.15,0.5]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg32_or_Trg32fb_onlyt35_Iso_pt_eta_bins' :{
    #     "SMALL": "eff.Trg_27_or_35_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32 fb only35t5)",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg32_or_Trg32fb_onlyt35_AIso_pt_bins_inc_eta': {
    #     "SMALL": "eff.Trg27_or_35_AIsoinc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32 fb only35t)| Iso_{rel} #in [0.15,0.5]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg32_onlyt35_Iso_pt_eta_bins' :{
    #     "SMALL": "eff.Trg_27_or_35_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 only35t5)",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg32_onlyt35_AIso_pt_bins_inc_eta': {
    #     "SMALL": "eff.Trg27_or_35_AIsoinc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 only35t)| Iso_{rel} #in [0.15,0.5]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg35_onlyt35_Iso_pt_eta_bins' :{
    #     "SMALL": "eff.Trg_27_or_35_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 35 only35t5)",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg27_or_Trg35_onlyt35_AIso_pt_bins_inc_eta': {
    #     "SMALL": "eff.Trg27_or_35_AIsoinc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 35 only35t)| Iso_{rel} #in [0.15,0.5]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg_onlyt35_Iso_pt_eta_bins' :{
    #     "SMALL": "eff.Trg_27_or_35_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32 fb or 35 only35t5)",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     'Trg_onylt35_AIso_pt_bins_inc_eta': {
    #     "SMALL": "eff.Trg27_or_35_AIsoinc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele(27 or 32 or 32 fb or 35 only35t5)| Iso_{rel} #in [0.15,0.5]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     "Trg32_AIso1_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg32_AIso1inc",
    #     "DIR": dir,
    #     "TITLE": "Trg El32eta2p1WPTight | Iso_{rel} #in [0.10,0.20]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     "Trg32_AIso2_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg32_AIso2inc",
    #     "DIR": dir,
    #     "TITLE": "Trg El32eta2p1WPTight | Iso_{rel} #in [0.20,0.50]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     "LooseIso_pt_eta_bins": {
    #     "SMALL": "eff.Iso",
    #     "DIR": dir,
    #     "TITLE": "Iso_{rel} < 0.15",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     "AIso2_pt_eta_bins": {
    #     "SMALL": "eff.Iso",
    #     "DIR": dir,
    #     "TITLE": "Iso_{rel} #in [0.20,0.50]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    #     "Trg_AIso2_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg_AIso2inc",
    #     "DIR": dir,
    #     "TITLE": "Trg Ele27eta2p1WPTight | Iso_{rel} #in [0.20,0.50]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "Trg32_Iso_pt_eta_bins": {
    #     "SMALL": "eff.Trg32_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg El32eta2p1WPTight",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "Trg32_or_Trg35_Iso_pt_eta_bins": {
    #     "SMALL": "eff.Trg",
    #     "DIR": dir,
    #     "TITLE": "Trg El32eta2p1WPTight or Trg El35eta2p1WPTight",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_pt_eta_bins": {
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDSanityCutbased_pt_eta_bins": {
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 for Sanity ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_0_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 0 ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_1_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 1  ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_2_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 2",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_3_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 3  ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_4_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 4 ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_5_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 5 ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_6_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 6 ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
    # "IDCutbased_step_7_pt_eta_bins":{
    #     "SMALL": "eff.ID",
    #     "DIR": dir,
    #     "TITLE": "Non-trig Cutbased ID 17 Step 7  ",
    #     "BKG": "CMSShape",
    #     "SIG": "DoubleVCorr"
    # },
        # "Trg35_AIso1_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg35_AIso1inc",
    #     "DIR": dir,
    #     "TITLE": "Trg El35eta2p1WPTight | Iso_{rel} #in [0.10,0.20]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "Trg35_AIso2_pt_bins_inc_eta": {
    #     "SMALL": "eff.Trg35_AIso2inc",
    #     "DIR": dir,
    #     "TITLE": "Trg El35eta2p1WPTight | Iso_{rel} #in [0.20,0.50]",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
    # "Trg35_Iso_pt_eta_bins": {
    #     "SMALL": "eff.Trg35_Iso",
    #     "DIR": dir,
    #     "TITLE": "Trg El35eta2p1WPTight",
    #     "BKG": "Exponential",
    #     "SIG": "DoubleVCorr"
    # },
}
mu_sliceing = {
    "ID_pt_eta_bins": {
        "SMALL": "eff.ID",
        "DIR": dir,
        "TITLE": "Medium ID",
        "BKG": "CMSShape",
        "SIG": "DoubleVCorr",
        "y_range": [0.8,1.0],
        "ratio_y_range": [0.9,1.1]
    },
    "Iso_pt_eta_bins": {
        "SMALL": "eff.Iso",
        "DIR": dir,
        "TITLE": "Iso_{rel} < 0.15",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.6,1.0],
        "ratio_y_range": [0.9,1.1]
    },
    "AIso1_pt_eta_bins": {
        "SMALL": "eff.AIso1",
        "DIR": dir,
        "TITLE": "Iso_{rel} #in [0.15,0.25]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,0.4],
        "ratio_y_range": [0.02,1.98]
    },
    "AIso2_pt_eta_bins": {
        "SMALL": "eff.AIso2",
        "DIR": dir,
        "TITLE": "Iso_{rel} #in [0.25,0.50]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,0.4],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg24_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu24",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg_IsoMu27_or_IsoMu24_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg IsoMu24 or IsoMu27",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    }
}

el_sliceing = {
    "ID90_pt_eta_bins": {
        "SMALL": "eff.ID90",
        "DIR": dir,
        "TITLE": "MVA ID 17 WP90",
        "BKG": "CMSShape",
        "SIG": "DoubleVCorr",
        "y_range": [0.4,1.05],
        "ratio_y_range": [0.8,1.2]
    },
    "ID80_pt_eta_bins": {
        "SMALL": "eff.ID80",
        "DIR": dir,
        "TITLE": "MVA ID 17 WP80",
        "BKG": "CMSShape",
        "SIG": "DoubleVCorr",
        "y_range": [0.4,1.05],
        "ratio_y_range": [0.8,1.2]
    },
    "Iso_pt_eta_bins": {
        "SMALL": "eff.Iso",
        "DIR": dir,
        "TITLE": "Iso_{rel} < 0.15",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.6,1.05],
        "ratio_y_range": [0.8,1.2]
    },
    "AIso1_pt_eta_bins": {
        "SMALL": "eff.AIso1",
        "DIR": dir,
        "TITLE": "Iso_{rel} #in [0.10,0.20]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,0.4],
        "ratio_y_range": [0.02,1.98]
    },
    "AIso2_pt_eta_bins": {
        "SMALL": "eff.AIso2",
        "DIR": dir,
        "TITLE": "Iso_{rel} #in [0.20,0.50]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,0.4],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele25",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_AIso1inc",
        "DIR": dir,
        "TITLE": "Trg Ele25 | Iso_{rel} #in [0.10,0.20]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele25 | Iso_{rel} #in [0.20,0.50]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg35_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele35",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg35_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg35_AIso1inc",
        "DIR": dir,
        "TITLE": "Trg Ele35 | Iso_{rel} #in [0.10,0.20]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg35_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg35_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele35 | Iso_{rel} #in [0.20,0.50]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg32_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele32",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.95,1.2]
    },
    "Trg32_AIso1_pt_bins_inc_eta": {
        "SMALL": "eff.Trg32_AIso1inc",
        "DIR": dir,
        "TITLE": "Trg Ele32 | Iso_{rel} #in [0.10,0.20]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg32_AIso2_pt_bins_inc_eta": {
        "SMALL": "eff.Trg32_Iso",
        "DIR": dir,
        "TITLE": "Trg Ele32 | Iso_{rel} #in [0.20,0.50]",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.02,1.98]
    },
    "Trg32_or_Trg35_Iso_pt_eta_bins": {
        "SMALL": "eff.Trg",
        "DIR": dir,
        "TITLE": "Trg Ele32 or Trg Ele35",
        "BKG": "Exponential",
        "SIG": "DoubleVCorr",
        "y_range": [0.0,1.0],
        "ratio_y_range": [0.1,1.9]
    },

}
if args.fit:
    if "m" in args.channel:
        for label in parameters.keys():
            pass
            if "sm" in args.channel:
                filename = ["output_17_5/ZmmTP_Embedding.root", "output_17_5/ZmmTP_Data_sm.root", "output_17_5/ZmmTP_DY.root"]
            else:
                filename = ["output_17_5/ZmmTP_Embedding.root", "output_17_5/ZmmTP_Data.root", "output_17_5/ZmmTP_DY.root"]
            dir_ext = ["/embedding", "/data", "/DY"]
            for i, file in enumerate(filename):
                try:
                    fitTagAndProbe_script.main(
                        filename=file,
                        name=label,
                        sig_model=parameters[label]["SIG"],
                        bkg_model=parameters[label]["BKG"],
                        title=parameters[label]["TITLE"],
                        particle="m",
                        isMC=False,
                        postfix="",
                        plot_dir=dir + label + dir_ext[i],
                        bin_replace=None)
                except AttributeError:
                    pass
                
        # electron plots
    elif "e" in args.channel:
        filename = ["output_17_5/ZeeTP_Embedding.root", "output_17_5/ZeeTP_Data.root", "output_17_5/ZeeTP_DYJetsToLL.root"]
        dir_ext = ["/embedding", "/data", "/DY"]
        # Parallel(n_jobs=num_cores)(delayed(fitTagAndProbe_script.main(
        #                 filename=file,
        #                 name=label,
        #                 sig_model=el_parameters[label]["SIG"],
        #                 bkg_model=el_parameters[label]["BKG"],
        #                 title=el_parameters[label]["TITLE"],
        #                 particle="e",
        #                 isMC=False,
        #                 postfix="",
        #                 plot_dir=dir + label + dir_ext[i],
        #                 bin_replace=None)) for label in el_parameters.keys())
        for label in el_parameters.keys():
            #filename = ["output/ZeeTP_Embedding.root", "output/ZeeTP_Data.root", "output/ZeeTP_DYJetsToLL.root"]
            #dir_ext = ["/embedding", "/data", "/DY"]
            for i, file in enumerate(filename):
                try:
                    fitTagAndProbe_script.main(
                        filename=file,
                        name=label,
                        sig_model=el_parameters[label]["SIG"],
                        bkg_model=el_parameters[label]["BKG"],
                        title=el_parameters[label]["TITLE"],
                        particle="e",
                        isMC=False,
                        postfix="",
                        plot_dir=dir + label + dir_ext[i],
                        bin_replace=None)
                except AttributeError:
                    pass
if args.plot:
    if "m" in args.channel:
        for label in mu_sliceing.keys():
            files = ["output_17_5/ZmmTP_Data_sm_Fits_" + label + ".root",
                    "output_17_5/ZmmTP_Embedding_Fits_" + label + ".root",
                    "output_17_5/ZmmTP_DY_Fits_" + label + ".root"
                    ]
            draw_options = [
                {
                    'Title':'Data'},
                {
                    'MarkerColor':4,
                    'LineColor':4,
                    'MarkerStyle':21,
                    'Title':"#mu#rightarrow#mu embedded"},
                {
                    'MarkerColor':2,
                    'LineColor':2,
                    'MarkerStyle':21,
                    'Title':"Z#rightarrow#mu#mu simulation"}
                    ]
            try:
                plotEffSlices_script.main(
                    files=files,
                    label=label,
                    draw_options=draw_options,
                    output="efficiency", 
                    title= mu_sliceing[label]["TITLE"], 
                    y_range= mu_sliceing[label]["y_range"], 
                    ratio_y_range= mu_sliceing[label]["ratio_y_range"], 
                    binned_in= "#eta", 
                    x_title= "Muon p_{T} (GeV)", 
                    ratio_to= 0, 
                    plot_dir= dir + label, 
                    label_pos= 3)
            except ReferenceError:
                print label + " Fits do not exist"
                pass
    elif "e" in args.channel:
        for label in el_sliceing.keys():
            files = ["output_17_5/ZeeTP_Data_Fits_" + label + ".root",
                    "output_17_5/ZeeTP_Embedding_Fits_" + label + ".root",
                    "output_17_5/ZeeTP_DYJetsToLL_Fits_" + label + ".root"
                    ]
            draw_options = [
                {
                    'Title':'Data'},
                {
                    'MarkerColor':4,
                    'LineColor':4,
                    'MarkerStyle':21,
                    'Title':"#mu#rightarrow e embedded"},
                {
                    'MarkerColor':2,
                    'LineColor':2,
                    'MarkerStyle':21,
                    'Title':"Z#rightarrow ee simulation"}
                    ]
            try:
                plotEffSlices_script.main(
                    files=files,
                    label=label,
                    draw_options=draw_options,
                    output="efficiency", 
                    title= el_sliceing[label]["TITLE"],# + "Efficiency" , 
                    y_range= el_sliceing[label]["y_range"], 
                    ratio_y_range= el_sliceing[label]["ratio_y_range"], 
                    binned_in= "#eta", 
                    x_title= "Electron p_{T} (GeV)", 
                    ratio_to= 0, 
                    plot_dir= dir + label, 
                    label_pos= 3)
            except ReferenceError:
                print label + " Fits do not exist"
                pass

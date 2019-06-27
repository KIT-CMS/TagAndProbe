import ROOT
import glob
import sys
# import json
import argparse
from array import array
import analysis as analysis

ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)

parser = argparse.ArgumentParser()
parser.add_argument('--era', default='2017')
args = parser.parse_args()

bin_cfgs_2017 = [
    {
        'name': 'ID90_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t',
        #'tag': 'id_90_t',
        'probe': 'id_90_p',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },
    {
        'name': 'ID80_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_80_t',
        #'tag': 'id_80_t',
        'probe': 'id_80_p',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'ID90_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t',
        #'tag': 'id_90_t',
        'probe': 'id_90_p ',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Iso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t && id_90_p',
        #'tag': 'id_90_t',
        'probe': 'iso_p < 0.15 ',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },
    {
        'name': 'Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t && id_90_p',
        #'tag': 'id_90_t',
        'probe': 'iso_p < 0.15 ',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t && id_90_p',
        #'tag': 'id_90_t',
        'probe': 'iso_p >= 0.15 ',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },
    {
        'name': 'AIso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t && id_90_p',
        #'tag': 'id_90_t',
        'probe': 'iso_p >= 0.15 ',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15., 20., 24., 26., 28., 30., 32., 34., 36., 38., 40., 45., 50., 100., 200., 1000.],
        #'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg_Iso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p', 
        'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32|| trg_p_Ele32_fb)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },
    {
        'name': 'Trg_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32|| trg_p_Ele32_fb)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32|| trg_p_Ele32_fb)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg27_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg27_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg32_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele32)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg32_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele32)',
        'binvar_x': 'pt_p',
         #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg32_fb_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele32_fb)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg32_fb_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele32_fb)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg35_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele35)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg35_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele35)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg27_or_Trg32_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele27 || trg_p_Ele32)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg27_or_Trg32_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele27 || trg_p_Ele32)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg27_or_Trg35_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele35 || trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg27_or_Trg35_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele35 || trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg27_or_Trg32_or_Trg35_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele35 || trg_p_Ele32 || trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg27_or_Trg32_or_Trg35_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele35 || trg_p_Ele32 || trg_p_Ele27)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },

    {
        'name': 'Trg32_or_Trg35_Iso_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15 && id_90_p',
        'probe': '(trg_p_Ele32 || trg_p_Ele35)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    },
    {
        'name': 'Trg32_or_Trg35_AIso_pt_bins_inc_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_Ele35 && pt_t >= 36 && id_90_t && iso_p >= 0.15 && id_90_p',
        'probe': '(trg_p_Ele32 || trg_p_Ele35)',
        'binvar_x': 'pt_p',
        #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
        'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 2.4]
    },
    

    # {
    #     'name': 'Trg27_or_Trg32_or_Trg32fb_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg27_or_Trg32_or_Trg32fb_AIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg27_or_Trg32_or_Trg32fb_onlyt35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg27_or_Trg32_or_Trg32fb_onlyt35_AIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p >= 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },

    #  {
    #     'name': 'Trg27_or_Trg32_onlyt35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg27_or_Trg32_onlyt35_AIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p >= 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele32)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },

    # {
    #     'name': 'Trg27_or_Trg35_onlyt35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele35 || trg_p_Ele27)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg27_or_Trg35_onlyt35_AIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p >= 0.15',
    #     'probe': '(trg_p_Ele35 || trg_p_Ele27)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    #     {
    #     'name': 'Trg_onlyt35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg_onylt35_AIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35) &&  id_90_t && iso_p >= 0.15',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32|| trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    #######
    ## Older unused scalefactors
    ########
    #     {
    #     'name': 'Trg32_or_Trg35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32) &&  id_90_t && iso_p < 0.15',
    #     'probe': '(trg_p_Ele35 || trg_p_Ele32)',
    #     'binvar_x': 'pt_p',
    #     #'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 31, 32., 33., 34., 35., 36., 37., 38., 39., 40., 42., 44., 46., 48., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    #     {
    #     'name': 'LooseIso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele27 || trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32|| trg_t_Ele32_fb) &&  id_90_t',
    #     #'tag': 'id_90_t',
    #     'probe': 'iso_p < 0.15',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    #     {
    #     'name': 'Trg_AIso2_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele27 || trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32|| trg_t_Ele32_fb) &&  id_90_t && iso_p >= 0.20 && iso_p < 0.50',
    #     'probe': '(trg_p_Ele27 || trg_p_Ele35 || trg_p_Ele32 || trg_p_Ele32_fb)',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 26., 27., 28., 29., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'AIso2_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele27 || trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32|| trg_t_Ele32_fb) &&  id_90_t',
    #     #'tag': 'id_90_t',
    #     'probe': 'iso_p >= 0.20 && iso_p < 0.50',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 40., 50., 100., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'AIso2_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele27 || trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32|| trg_t_Ele32_fb) &&  id_90_t',
    #     #'tag': 'id_90_t',
    #     'probe': 'iso_p >= 0.20 && iso_p < 0.50',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 40., 50., 100., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'LooseIso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele27 || trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32|| trg_t_Ele32_fb) &&  id_90_t',
    #     #'tag': 'id_90_t',
    #     'probe': 'iso_p < 0.15',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'IDCutbased_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t',
    #     'probe': 'id_cutbased_p',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDSanityCutbased_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_sanity_t',
    #     'probe': 'id_cutbased_sanity_p',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_0_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_0',
    #     'probe': 'id_cutbased_t_step_0',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_1_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_1',
    #     'probe': 'id_cutbased_p_step_1',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_2_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_2',
    #     'probe': 'id_cutbased_p_step_2',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_3_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_3',
    #     'probe': 'id_cutbased_p_step_3',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_4_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_4',
    #     'probe': 'id_cutbased_p_step_4',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_5_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_5',
    #     'probe': 'id_cutbased_p_step_5',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_6_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_6',
    #     'probe': 'id_cutbased_p_step_6',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'IDCutbased_step_7_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele27 && id_cutbased_t_step_7',
    #     'probe': 'id_cutbased_p_step_7',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 15., 20., 25., 30., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg35_Iso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.10',
    #     'probe': 'trg_p_Ele35',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg35_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p < 0.10',
    #     'probe': 'trg_p_Ele35',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg35_AIso1_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.10 && iso_p < 0.20',
    #     'probe': 'trg_p_Ele35',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg35_AIso2_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele35 && pt_t >= 36 &&  id_90_t && iso_p >= 0.20 && iso_p < 0.50',
    #     'probe': 'trg_p_Ele35',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg32_Iso_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele32 &&  id_90_t && iso_p < 0.10',
    #     'probe': 'trg_p_Ele32',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg32_Iso_pt_eta_bins',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele32 &&  id_90_t && iso_p < 0.10',
    #     'probe': 'trg_p_Ele32',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0.0, 1.0, 1.4442, 1.56, 2.1, 2.5]
    # },
    # {
    #     'name': 'Trg32_AIso1_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele32 &&  id_90_t && iso_p >= 0.10 && iso_p < 0.20',
    #     'probe': 'trg_p_Ele32',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg32_AIso2_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': 'trg_t_Ele32 &&  id_90_t && iso_p >= 0.20 && iso_p < 0.50',
    #     'probe': 'trg_p_Ele32',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },
    # {
    #     'name': 'Trg32_or_Trg35_pt_bins_inc_eta',
    #     'var': 'm_ll(50,65,115)',
    #     'tag': '(trg_t_Ele35 && pt_t >= 36 || trg_t_Ele32) &&  id_90_t && iso_p < 0.10',
    #     'probe': '(trg_p_Ele35 || trg_p_Ele32)',
    #     'binvar_x': 'pt_p',
    #     'bins_x': [10., 20., 25., 30., 34., 36., 38., 40., 50., 100., 200., 1000.],
    #     'binvar_y': 'abs(eta_p)',
    #     'bins_y': [0, 2.4]
    # },

]

if args.era=='2016': 
	bin_cfgs=[cfg for cfg in bin_cfgs_2016]
elif args.era=='2017':
	bin_cfgs=[cfg for cfg in bin_cfgs_2017]
else:
	raise ValueError("Please select era: 2016 or 2017")

drawlist = []
andable = set()

for cfg in bin_cfgs:
    cfg['hist'] = ROOT.TH2D(cfg['name'], cfg['name'],
                            len(cfg['bins_x'])-1, array('d', cfg['bins_x']),
                            len(cfg['bins_y'])-1, array('d', cfg['bins_y']))
    hist = cfg['hist']
    hist.GetXaxis().SetTitle(cfg['binvar_x'])
    hist.GetYaxis().SetTitle(cfg['binvar_y'])

    cfg['bins'] = []

    for i in xrange(1, hist.GetNbinsX()+1):
        for j in xrange(1, hist.GetNbinsY()+1):
            cfg['bins'].append('%s>=%g && %s<%g && %s>=%g && %s<%g' % (
                cfg['binvar_x'], hist.GetXaxis().GetBinLowEdge(i),
                cfg['binvar_x'], hist.GetXaxis().GetBinUpEdge(i),
                cfg['binvar_y'], hist.GetYaxis().GetBinLowEdge(j),
                cfg['binvar_y'], hist.GetYaxis().GetBinUpEdge(j),
                ))
            andable.add('%s>=%g' % (cfg['binvar_x'], hist.GetXaxis().GetBinLowEdge(i)))
            andable.add('%s<%g' % (cfg['binvar_x'], hist.GetXaxis().GetBinUpEdge(i)))
            andable.add('%s>=%g' % (cfg['binvar_y'], hist.GetYaxis().GetBinLowEdge(j)))
            andable.add('%s<%g' % (cfg['binvar_y'], hist.GetYaxis().GetBinUpEdge(j)))

    for b in cfg['bins']:
        drawlist.append((cfg['var'], '((%s) && !(%s) && (%s))' % (b, cfg['probe'], cfg['tag'])))
        drawlist.append((cfg['var'], '((%s) && (%s) && (%s))' % (b, cfg['probe'], cfg['tag'])))
        andable.add(cfg['probe'])
        andable.add(cfg['tag'])


trees = {
    'DYJetsToLL': analysis.TTreeEvaluator('ee_singleelectron_nominal/ntuple', '/ceph/jbechtel/2018/scalefactors/DYJetsToLLM50_RunIIAutumn18MiniAOD_102X_13TeV_MINIAOD_madgraph-pythia8_v1/DYJetsToLLM50_RunIIAutumn18MiniAOD_102X_13TeV_MINIAOD_madgraph-pythia8_v1.root'),
    'Data': analysis.TTreeEvaluator('ee_singleelectron_nominal/ntuple', '/ceph/jbechtel/2018/scalefactors/EGamma_Run2018C_17Sep2018v1_13TeV_MINIAOD/EGamma_Run2018C_17Sep2018v1_13TeV_MINIAOD.root'),
    'Embedding':  analysis.TTreeEvaluator('ee_singleelectron_nominal/ntuple', '/ceph/jbechtel/2018/scalefactors/Embedding2018C_ElectronEmbedding_inputDoubleMu102XminiAODv1_13TeV_USER_v1/Embedding2018C_ElectronEmbedding_inputDoubleMu102XminiAODv1_13TeV_USER_v1.root')

}   

for sample in trees:
    outfile = ROOT.TFile('output_17_5/ZeeTP_%s.root' % sample, 'RECREATE')
    hists = trees[sample].Draw(drawlist, compiled=True)

    i = 0

    for cfg in bin_cfgs:
        wsp = ROOT.RooWorkspace('wsp_'+cfg['name'], '')
        var = wsp.factory('m_ll[100,65,115]')

        outfile.cd()
        outfile.mkdir(cfg['name'])
        ROOT.gDirectory.cd(cfg['name'])

        for b in cfg['bins']:
            hists[2*i].SetName(b+':fail')
            hists[2*i+1].SetName(b+':pass')
            hists[2*i].Write()
            hists[2*i+1].Write()
            dat = wsp.imp(ROOT.RooDataHist(b, '', ROOT.RooArgList(var),
                          ROOT.RooFit.Index(wsp.factory('cat[fail,pass]')),
                          ROOT.RooFit.Import('fail', hists[2*i]),
                          ROOT.RooFit.Import('pass', hists[2*i+1]))
                          )
            i += 1
        outfile.cd()
        wsp.Write()
        cfg['hist'].Write()
        wsp.Delete()

    outfile.Close()

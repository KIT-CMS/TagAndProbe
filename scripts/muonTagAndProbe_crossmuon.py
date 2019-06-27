import ROOT
import glob
import sys
# import json
import argparse
from array import array
import UserCode.ICHiggsTauTau.analysis as analysis

ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)

parser = argparse.ArgumentParser()
parser.add_argument('--era', default='2017')
args = parser.parse_args()

bin_cfgs_2017 = [
    {
        'name': 'Trg_Mu20_pt_eta_bins',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_IsoMu24 && pt_t > 25 && iso_p < 0.15 && id_p && isAntiL1TauMatched_trg_p_mu20tau27>0.5',
        'probe': 'trg_p_mu20tau27',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15.,16.,17.,18.,19., 20.,21.,22.,23.,24., 25., 30., 35., 40., 45., 50., 60., 80., 100., 200., 1000.],
        'binvar_y': 'abs(eta_p)',
        'bins_y': [0, 0.9, 1.2, 2.1, 2.4]
    },
    {
        'name': 'Trg_Mu20_pt_incl_eta',
        'var': 'm_ll(50,65,115)',
        'tag': 'trg_t_IsoMu24 && pt_t > 25 && iso_p < 0.15 && id_p &&  isAntiL1TauMatched_trg_p_mu20tau27>0.5',
        'probe': 'trg_p_mu20tau27',
        'binvar_x': 'pt_p',
        'bins_x': [10., 15.,16.,17.,18.,19., 20.,21.,22.,23.,24., 25., 30., 35., 40., 45., 50., 60., 80., 100., 200., 1000.],
        'binvar_y': 'eta_p',
        'bins_y': [-2.4, 2.4]
    }
]

#if args.era=='2016': 
#	bin_cfgs=bin_cfgs_2016
if args.era=='2017':
	bin_cfgs=bin_cfgs_2017
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
        drawlist.append((cfg['var'], '((%s) && (%s) && (%s)) ' % (b, cfg['probe'], cfg['tag'])))
        andable.add(cfg['probe'])
        andable.add(cfg['tag'])


trees = {
    'Embedding': analysis.TTreeEvaluator('mm_crossmuon/ntuple', 'files_mu18tauXX/Embedding2018C_MuonEmbedding_inputDoubleMu102XminiAODv1_13TeV_USER_v1/Embedding2018C_MuonEmbedding_inputDoubleMu102XminiAODv1_13TeV_USER_v1.root'),
    'DY': analysis.TTreeEvaluator('mm_crossmuon/ntuple', 'files_mu18tauXX/DYJetsToLLM50_RunIIAutumn18MiniAOD_102X_13TeV_MINIAOD_madgraph-pythia8_v1/DYJetsToLLM50_RunIIAutumn18MiniAOD_102X_13TeV_MINIAOD_madgraph-pythia8_v1.root'),
    'Data_sm': analysis.TTreeEvaluator("mm_crossmuon/ntuple", 'files_mu18tauXX/SingleMuon_Run2018C_17Sep2018v1_13TeV_MINIAOD/SingleMuon_Run2018C_17Sep2018v1_13TeV_MINIAOD.root'),
   # 'Data': analysis.TTreeEvaluator('mm_new_nominal/ntuple', '/storage/9/sbrommer/artus_outputs/TPZmm/2018-11-06/output/DoubleMuon.root')
}
#trees = {
#    'Embedding': analysis.TTreeEvaluator('mm_crossmuon/ntuple', 'files_3/emb.root')#,
#    'DY': analysis.TTreeEvaluator('mm_crossmuon/ntuple', 'files_3/mc.root'),
#    'Data_sm': analysis.TTreeEvaluator("mm_crossmuon/ntuple", 'files_3/data.root'),
#}

        
for sample in trees:
    outfile = ROOT.TFile('output_crossmuon_testing/ZmmTP_%s.root' % sample, 'RECREATE')
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

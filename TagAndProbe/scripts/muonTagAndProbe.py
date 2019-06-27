import ROOT
import glob
import sys
import yaml
import os
import argparse
from array import array
import TagAndProbe.TagAndProbe.analysis as analysis

ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)

parser = argparse.ArgumentParser()
parser.add_argument('--era', default='2017')
args = parser.parse_args()


bin_cfgs = yaml.load(open("bins_{}.yaml".format(args.era)))

drawlist = []
andable = set()

for key,cfg in bin_cfgs.items():
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
    'Embedding': analysis.TTreeEvaluator('mm_singlemuon_nominal/ntuple', 'files/embedding2017.root'),
    'DY': analysis.TTreeEvaluator('mm_singlemuon_nominal/ntuple', 'files/dy2017.root'),
    'Data_sm': analysis.TTreeEvaluator("mm_singlemuon_nominal/ntuple", 'files/data2017.root'),
   # 'Data': analysis.TTreeEvaluator('mm_new_nominal/ntuple', '/storage/9/sbrommer/artus_outputs/TPZmm/2018-11-06/output/DoubleMuon.root')
}
        
for sample in trees:
    out_dir = "output"
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    outfile = ROOT.TFile('{}/ZmmTP_{}.root'.format(out_dir, sample), 'RECREATE')
    hists = trees[sample].Draw(drawlist, compiled=True)

    i = 0

    for key,cfg in bin_cfgs.items():
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

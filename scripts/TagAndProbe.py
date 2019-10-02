import ROOT
import glob
import sys
import yaml
import os
import argparse
from array import array
import UserCode.TagAndProbe.analysis as analysis

ROOT.RooWorkspace.imp = getattr(ROOT.RooWorkspace, 'import')
ROOT.TH1.AddDirectory(0)

parser = argparse.ArgumentParser()
parser.add_argument('--era', required = True)
parser.add_argument('--channel', required = True)
parser.add_argument('--output', default = "output", required = False)

args = parser.parse_args()
if "cross" in args.channel and args.era=="2016":
    print "No cross trigger settings available for 2016 yet."
    sys.exit()
bin_cfgs = yaml.load(open("settings/settings_{}_{}.yaml".format(args.channel,args.era)))
input_files = yaml.load(open("set_inputfiles.yaml"))


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

if args.channel == "embeddingselection":
    trees = {
        'Data': analysis.TTreeEvaluator(input_files[args.era][args.channel]['folder'], input_files[args.era][args.channel]['Data']),
    }
else:
    trees = {
        'Embedding': analysis.TTreeEvaluator(input_files[args.era][args.channel]['folder'], input_files[args.era][args.channel]['Embedding']),
        'old_emb': analysis.TTreeEvaluator(input_files[args.era][args.channel]['folder'], input_files[args.era][args.channel]['old_emb']),
        'DY': analysis.TTreeEvaluator(input_files[args.era][args.channel]['folder'], input_files[args.era][args.channel]['DY']),
        'Data': analysis.TTreeEvaluator(input_files[args.era][args.channel]['folder'], input_files[args.era][args.channel]['Data']),
    }
        
for sample in trees:
    out_dir = args.output
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    outfile = ROOT.TFile('{}/{}_TP_{}_{}.root'.format(out_dir, args.channel, sample, args.era), 'RECREATE')
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

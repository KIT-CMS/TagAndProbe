ntuplepath="/storage/gridka-nrg/sbrommer/CROWN/ntuples/tagandprobe_2022_07_v6/CROWNRun/2018"
resultpath="/ceph/sbrommer/embedding_ul/scalefactors/inputfiles/2018_v6"
mkdir -p $resultpath
echo "Merging files from $ntuplepath to $resultpath"
hadd $resultpath/ntuple_DYJets_ee_UL2018.root $ntuplepath/DYJetsToLL_*/ee/DYJetsToLL*
hadd $resultpath/ntuple_ElEmbedding_UL2018.root $ntuplepath/ElectronEmbedding*/ee/ElectronEmbedding*
hadd $resultpath/ntuple_MuEmbedding_UL2018.root $ntuplepath/MuonEmbedding*/mm/MuonEmbedding*
hadd $resultpath/ntuple_DYJets_mm_UL2018.root $ntuplepath/DYJetsToLL_*/mm/DYJetsToLL*
hadd $resultpath/ntuple_DoubleMuon_UL2018.root $ntuplepath/DoubleMuon_Run2018*/mm/*
hadd $resultpath/ntuple_SingleMuon_UL2018.root $ntuplepath/SingleMuon_Run2018*/mm/*                 
hadd $resultpath/ntuple_EGamma_UL2018.root $ntuplepath/EGamma_Run2018*/ee/*

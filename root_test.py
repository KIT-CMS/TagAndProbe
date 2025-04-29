import ROOT


f = ROOT.TFile.Open("output/electron_TP_DY_2018UL_Fits_Trg35_Iso_pt_eta_bins.root")

# TGraphAsymmErrors-Objekt laden
g = f.Get("gr_Trg35_Iso_pt_eta_bins_projx_3")  # Beispiel: Projektion 3

# Anzahl der Punkte im Graph
n = g.GetN()
print(n)
# Zugriff auf Werte und Fehler
for i in range(n):
    x = ROOT.Double()
    y = ROOT.Double()
    g.GetPoint(i, x, y)
    
    ex_low  = g.GetErrorXlow(i)
    ex_high = g.GetErrorXhigh(i)
    ey_low  = g.GetErrorYlow(i)
    ey_high = g.GetErrorYhigh(i)
    
    print(f"Point {i}: x = {x}, y = {y}, ex = [-{ex_low}, +{ex_high}], ey = [-{ey_low}, +{ey_high}]")

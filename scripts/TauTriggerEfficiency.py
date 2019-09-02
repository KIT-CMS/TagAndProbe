import logging
import argparse
import plotEffSlices_script
from TauTriggerEfficiency_script import TauLegEfficiencies


def parse_args():
    parser = argparse.ArgumentParser(description="To be filled.")
    parser.add_argument("-w", "--working-points", type=str,
                        nargs="+", default=["all"],
                        choices=["all", "vloose", "loose", "medium",
                                 "tight", "vtight", "vvtight"],
                        help="The MVA tau Id working points the"
                             " efficiencies should be calculated for.")
    parser.add_argument("-i", "--input-file", type=str, required=True,
                        help="The input file containing the ntuples.")
    parser.add_argument("-e", "--era", type=str, required=True,
                        help="Dataset era")
    parser.add_argument("-o", "--output-file", type=str,
                        default="output_ERA_tau_leg.root",
                        help="The output file. Defaults to %(default)s")
    parser.add_argument("-f", "--file-types", type=str, nargs="+",
                        choices=["DATA", "MC", "EMB"],
                        default=["DATA", "MC", "EMB"],
                        help="The sample types to be processed.")
    parser.add_argument("-t", "--triggers", type=str, nargs="+",
                        choices=["mutau", "etau", "tau35",
                                 "medtau40", "tighttau40",
                                 "hpstau35", "ditau",
                                 "ditauvbf",
                                 "TauLead", "TauTrail"],
                        default=["mutau", "etau", "ditau"],
                        help="The triggers to be processed.")
    parser.add_argument("--per-dm", action="store_true",
                        help="Activate decay mode splitting of the efficiencies.")
    parser.add_argument("--use-et", action="store_true",
                        help="Use measurement in et channel for etau cross trigger.")
    parser.add_argument('--fit', action="store_true")
    parser.add_argument('--plot', action="store_true")
    args = parser.parse_args()

    if "all" in args.working_points:
        args.working_points = ["vloose", "loose", "medium",
                               "tight", "vtight", "vvtight"]
    return args


def setup_logging(level=logging.WARNING):
    logging.basicConfig(level=level)


def main(args):
    wps = args.working_points
    triggers = args.triggers
    filetypes = args.file_types

    eff = TauLegEfficiencies(
            int(args.era),
            args.output_file,
            args.input_file,
            per_dm=args.per_dm,
            use_et=args.use_et
    )
    for wp in wps:
        eff.add_wp(wp)
    for trg in triggers:
        eff.add_trigger_name(trg)
    for ft in filetypes:
        eff.add_filetype(ft)
    eff.create_efficiencies()
    return


def make_plots(args):

    plot_dir = "plots"
    draw_options = [
        {
            'Title': 'Data'},
        {
            'MarkerColor': 2,
            'LineColor': 2,
            'MarkerStyle': 21,
            'Title': "MC"},
        {
            'MarkerColor': 4,
            'LineColor': 4,
            'MarkerStyle': 21,
            'Title': "Embedded"}

    ]

    era = args.era
    title = "tau leg"
    x_title = "p_{T} (#tau_{h}) (GeV)"
    plotEffSlices_script.plot_hadronic(
        input_file=args.output_file,
        triggers=args.triggers,
        working_points=args.working_points,
        file_types=args.file_types,
        era=era,
        draw_options=draw_options,
        output="tau_leg_efficiency",
        title=title,
        y_range=[0.0, 1.1],
        ratio_y_range=[0.0, 2.0],
        binned_in="#eta",
        x_title=x_title,
        ratio_to=0,
        plot_dir=plot_dir,
        label_pos=3)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    args = parse_args()
    if args.output_file == "output_ERA_tau_leg.root":
        args.output_file = "output_{}_tau_leg.root".format(args.era)
    if args.fit:
        main(args)
    if args.plot:
        make_plots(args)

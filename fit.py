import argparse
from pathlib import Path

import cabinetry
import hist
from cabinetry.contrib import histogram_reader

POI = "ttbar_norm"
# Start the fit at 110 GeV and merge pairs of bins, the same as the AGC
REBIN = slice(110j, None, hist.rebin(2))


def rebinning_router(config: dict) -> cabinetry.route.Router:
    """Router that reads each template and rebins it."""
    router = cabinetry.route.Router()
    general = config["General"]

    @router.register_template_builder()
    def build(region, sample, systematic, template):
        path = cabinetry.templates.collector._histo_path(
            general["InputPath"],
            general.get("VariationPath"),
            region,
            sample,
            systematic,
            template,
        )
        return hist.Hist(histogram_reader.with_uproot(path))[REBIN]

    return router


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the workspace and fit it")
    parser.add_argument("config", type=Path, help="cabinetry config")
    parser.add_argument("workspace", type=Path, help="Output pyhf workspace")
    parser.add_argument("figures", type=Path, help="Output folder for plots")
    args = parser.parse_args()

    config = cabinetry.configuration.load(args.config)
    cabinetry.templates.build(config, router=rebinning_router(config))
    cabinetry.templates.postprocess(config)
    ws = cabinetry.workspace.build(config)
    cabinetry.workspace.save(ws, args.workspace)

    model, data = cabinetry.model_utils.model_and_data(ws)
    fit_results = cabinetry.fit.fit(model, data)

    cabinetry.visualize.pulls(
        fit_results, exclude=POI, figure_folder=args.figures, close_figure=True
    )
    prefit = cabinetry.model_utils.prediction(model)
    postfit = cabinetry.model_utils.prediction(model, fit_results=fit_results)
    for prediction in (prefit, postfit):
        cabinetry.visualize.data_mc(
            prediction,
            data,
            config=config,
            figure_folder=args.figures,
            close_figure=True,
        )

    i = model.config.poi_index
    print(
        f"{POI}: {fit_results.bestfit[i]:.3f} +/- {fit_results.uncertainty[i]:.3f}"
    )


if __name__ == "__main__":
    main()

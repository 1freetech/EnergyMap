"""Tkinter UI smoke checks; run under xvfb-run on Linux."""
from energymap import EnergyMapApp, validate_site


def main():
    app = EnergyMapApp()
    try:
        app.update()
        assert len(app.tree.get_children()) >= 20, "Operating plants are missing"
        app.view.set("National top 10")
        app.refresh()
        app.update()
        assert len(app.tree.get_children()) == 10, "National ranking selection failed"
        app.view.set("State rankings")
        app.state.set("Texas")
        app.refresh()
        app.update()
        assert len(app.tree.get_children()) >= 3, "State filter failed"
        app.custom.append(validate_site({"name":"GUI smoke test", "state":"WA",
                                         "lat":47.5, "lon":-120.5, "capacityMW":50}))
        app.view.set("My map")
        app.refresh()
        app.update()
        assert len(app.tree.get_children()) >= 1, "My map selection failed"
        assert app.point_hits, "A valid custom map marker did not render"
        print("EnergyMap GUI smoke: operating/state/national/custom views and markers passed.")
    finally:
        app.destroy()


if __name__ == "__main__":
    main()

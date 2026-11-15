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
        states = list(app.state_combo["values"])
        assert len(set(states)) == 50, f"Expected 50 state ranking selectors; got {len(set(states))}"
        for state in states:
            app.state.set(state)
            app.refresh()
            app.update()
            assert app.tree.get_children(), f"No ranking rows for {state}"
            assert all(app.tree.set(row, "state") == state for row in app.tree.get_children()), (
                f"State filter leaked records from another state: {state}"
            )
        app.state.set("Texas")
        app.refresh()
        assert len(app.tree.get_children()) >= 3, "Texas rankings missing"
        app.search.set("no-match-expected-energymap-gui-smoke")
        app.update()
        assert not app.tree.get_children(), "Search failed to filter rows"
        app.search.set("")
        app.update()
        assert app.tree.get_children(), "Clearing search did not restore rows"
        app.custom.append(validate_site({"name": "GUI smoke test", "state": "WA",
                                         "lat": 47.5, "lon": -120.5, "capacityMW": 50}))
        app.view.set("My map")
        app.refresh()
        app.update()
        assert any(app.tree.set(row, "name") == "GUI smoke test"
                   for row in app.tree.get_children()), "Custom site not listed"
        assert app.point_hits, "A valid custom map marker did not render"
        print("EnergyMap GUI smoke: operating, national, all 50 states, search, custom marker passed.")
    finally:
        app.destroy()


if __name__ == "__main__":
    main()

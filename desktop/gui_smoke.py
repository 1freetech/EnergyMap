"""Full interface smoke test under Linux Xvfb; real repo datasets required."""
from energymap import EnergyMapApp


def main():
    app = EnergyMapApp()
    try:
        app.update()
        assert len(app.tree.get_children()) >= 20, 'Operating plants missing'
        assert len(app.atlas.states) >= 50, 'US state boundaries missing'
        assert len(app.atlas.countries) >= 175, 'World country boundaries missing'
        assert len(app.atlas.point_hits) >= 20, 'Operating site markers missing'
        assert app.cols == ('rank', 'name', 'state', 'capacity')
        assert app.info.cget('wrap') == 'word'
        app.atlas.mode.set('World globe')
        app.atlas.change_mode()
        app.update()
        assert app.atlas.canvas.find_all(), 'Globe failed to render'
        assert app.atlas.point_hits, 'Visible hemisphere must include US pins at initial angle'
        start = app.atlas.globe_lon
        app.atlas._spin()
        assert app.atlas.globe_lon != start, 'Globe did not rotate'
        app.atlas.stop_spin()
        app.atlas.mode.set('United States')
        app.atlas.change_mode()
        app.view.set('National top 10')
        app._change_view()
        assert len(app.tree.get_children()) == 10, 'National ranking failed'
        app.view.set('State rankings')
        app._change_view()
        states = list(app.state_combo['values'])
        assert len(set(states)) == 50, 'Expected 50 states'
        for state in states:
            app.state.set(state)
            app.refresh()
            assert app.tree.get_children(), f'No rankings for {state}'
        app.search.set('does-not-match-any-record-ever')
        app.update()
        assert not app.tree.get_children(), 'Search did not filter rows'
        app.search.set('')
        app.update()
        assert app.tree.get_children(), 'Clear search failed'
        app.geometry('1000x640')
        app.update()
        assert app.atlas.canvas.winfo_width() > 250
        assert app.tree.winfo_width() > 250
        print('EnergyMap UI smoke: U.S. basemap, globe spin, records, rankings, search, resize passed')
    finally:
        app.destroy()


if __name__ == '__main__':
    main()

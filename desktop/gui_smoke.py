"""Full interface smoke test under Linux Xvfb; real repo datasets required."""
from energymap import EnergyMapApp


def main():
    app = EnergyMapApp()
    try:
        app.update()
        assert len(app.tree.get_children()) == 459, 'Canonical All sites registry not loaded'
        assert app.view.get() == 'All sites'
        assert len(app.catalogs['All ≥1 GW']) == 373, 'Threshold filter must include development records'
        assert len(app.catalogs['Data centers']) == 156
        assert len(app.catalogs['Data centers ≥1 GW']) == 70
        app.view.set('All ≥1 GW')
        app._change_view()
        assert len(app.tree.get_children()) == 373
        first = app.visible[app.tree.get_children()[0]]['capacityMW']
        second = app.visible[app.tree.get_children()[1]]['capacityMW']
        assert first >= second, 'Default MW sort is not descending'
        app.change_sort('capacity')
        assert app.visible[app.tree.get_children()[0]]['capacityMW'] <= 1000
        app.change_sort('capacity')
        assert len(app.atlas.states) >= 50, 'US state boundaries missing'
        assert len(app.atlas.countries) >= 175, 'World country boundaries missing'
        assert len(app.atlas.point_hits) >= 270, 'Power-generation markers missing'
        assert app.cols == ('rank', 'name', 'state', 'category', 'capacity')
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
        assert len(set(states)) == 51, 'Expected All states plus 50 states'
        for state in states:
            if state == 'All states':
                continue
            app.state.set(state)
            app.refresh()
            assert app.tree.get_children(), f'No rankings for {state}'
        app.state.set('All states')
        app.view.set('Data centers')
        app._change_view()
        assert len(app.tree.get_children()) == 156, 'All state development sites must be browsable'
        app.view.set('National top 10')
        app._change_view()
        assert len(app.tree.get_children()) == 10, 'All national projects must be browsable'
        app.change_sort('rank')
        assert app.visible[app.tree.get_children()[0]]['nationalRank'] == 1
        app.view.set('All sites')
        app._change_view()
        app.category.set('Data centers / campuses')
        app.refresh()
        assert len(app.tree.get_children()) == 156, 'Category filter leaked power plants'
        app.category.set('All categories')
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
